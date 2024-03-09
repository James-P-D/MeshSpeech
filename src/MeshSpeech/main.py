from geopy.geocoders import Nominatim # pip install geopy
import PySimpleGUI as sg
import meshtastic.serial_interface
from pubsub import pub
import speech_recognition as sr
import pyttsx3

resolve_location_mode = True
speech_to_text_mode = True
text_to_speech_mode = True
currently_recording = False

sg.theme("Default1")

device_label = sg.Text("Device")
device_textbox = sg.InputText(font="Courier 10", default_text="", size=(35, 1))
connect_device_button = sg.Button("Connect")

resolve_location_toggle = sg.Checkbox("Resolve Address", default=False, key="resolve_address_toggle",
                                      enable_events=True)
speech_to_text_toggle = sg.Checkbox("Speech to Text", default=False, key="speech_to_text_toggle", enable_events=True)
text_to_speech_toggle = sg.Checkbox("Text to Speech", default=False, key="text_to_speech_toggle", enable_events=True)

record_button = sg.Button("Record")

target_input_label = sg.Text("Target")
target_input_combo = sg.Combo([], size=(20, 1))

message_input_label = sg.Text("Message")
message_input_textbox = sg.InputText(font="Courier 10", key="message_input_textbox", size=(35, 1))
message_input_button = sg.Button("Send")

message_log_label = sg.Text("Message Log")
message_log_textbox = sg.Multiline(size=(50, 10), font="Courier 10")

resolve_location_toggle.Disabled = True
speech_to_text_toggle.Disabled = True
text_to_speech_toggle.Disabled = True
message_log_textbox.Disabled = True
message_input_textbox.Disabled = True
message_input_button.Disabled = True
target_input_combo.Disabled = True
record_button.Disabled = True

main_layout = [[device_label, device_textbox, connect_device_button],
               [speech_to_text_toggle, text_to_speech_toggle, resolve_location_toggle],
               [record_button],
               [message_input_label, message_input_textbox, message_input_button],
               [target_input_label, target_input_combo],
               [message_log_label],
               [message_log_textbox]]

main_window = sg.Window("Meshtastic Speech Client", main_layout, icon="meshtastic.ico", finalize=True)
main_window["message_input_textbox"].bind("<Return>", "_Enter")

iface = None
speech_recognizer = sr.Recognizer()

##################################################################


def onReceive(packet, interface):
    if packet:
        if packet["decoded"]["portnum"] == "TEXT_MESSAGE_APP":
            sender_node = None
            for node in iface.nodes.values():
                if node["num"] == packet["from"]:
                    sender_node = node
            payload = f"{packet['decoded']['payload'].decode('ascii')}"
            if sender_node:
                add_debug_line(f"{sender_node['user']['shortName']}> {payload}")
                if text_to_speech_mode:
                    speak_text(f"Message {payload}\n"
                               f"received from "
                               f"{sender_node['user']['shortName'][0]} "
                               f"{sender_node['user']['shortName'][1]} "
                               f"{sender_node['user']['shortName'][2]} "
                               f"{sender_node['user']['shortName'][3]} ")
                if resolve_location_mode:
                    if 'position' in sender_node.keys():
                        if ('latitude' in sender_node['position'].keys()) and\
                                ('longitude' in sender_node['position'].keys()):
                            sender_address = get_address(sender_node['position']['latitude'],
                                                         sender_node['position']['longitude'])
                            if sender_address:
                                add_debug_line(f"{sender_node['user']['shortName']} location> {sender_address}")
                                if text_to_speech_mode:
                                    speak_text(f"{sender_address}")
            else:
                add_debug_line(f"UNKNOWN> packet['decoded']['payload']")
                if text_to_speech_mode:
                    speak_text(f"Message {payload}\nreceived from unknown node")


def get_address(latitude, longitude):
    try:
        geolocator = Nominatim(user_agent="MeshSpeech")
        return geolocator.reverse(f"{latitude}, {longitude}")
    except Exception as e:
        sg.popup(f"Error resolving address:\n\n{e}", title="Error", icon="meshtastic.ico")
        return ""

##################################################################

def add_debug_line(s):
    current_debug_lines = main_window[message_log_textbox.key].get()
    if current_debug_lines:
        current_debug_lines = current_debug_lines + "\n"
    message_log_textbox.update(current_debug_lines + s)
    message_log_textbox.set_vscroll_position(1.0)  # Scroll to bottom

##################################################################

def speak_text(t):
    engine = pyttsx3.init()
    engine.say(t)
    engine.runAndWait()

pub.subscribe(onReceive, "meshtastic.receive")
while True:
    event, values = main_window.read(timeout=100)

    if event == sg.WIN_CLOSED:
        if iface:
            iface.close()
        break

    elif event == "Connect":
        try:
            iface = meshtastic.serial_interface.SerialInterface(devPath=values[device_textbox.key])

            add_debug_line(f"INFO> Connected to {iface.getMyNodeInfo()['user']['longName']} ({iface.getMyNodeInfo()['user']['shortName']})")

            node_names = ["BROADCAST"]
            if iface.nodes:
                for n in iface.nodes.values():
                    node_names.append(n["user"]["longName"])

            device_textbox.update(disabled=True)
            connect_device_button.update(disabled=True)

            resolve_location_toggle.update(disabled=False)
            speech_to_text_toggle.update(disabled=False)
            text_to_speech_toggle.update(disabled=False)

            record_button.update(disabled=False)

            target_input_combo.update(disabled=False)
            target_input_combo.update(values=node_names)
            target_input_combo.update(set_to_index=0)

            message_input_textbox.update(disabled=False)
            message_input_button.update(disabled=False)
        except Exception as e:
            sg.popup(f"Communication error:\n\n{e}", title="Error", icon="meshtastic.ico")

    elif (event == "Send") or (event == "message_input_textbox" + "_Enter"):
        selected_target = values[target_input_combo.key]
        message = values[message_input_textbox.key]
        if selected_target == "BROADCAST":
            iface.sendText(message)
            add_debug_line(f"{iface.getMyNodeInfo()['user']['shortName']} (Broadcast)> {message}")
        else:
            target_id = -1
            if iface.nodes:
                for n in iface.nodes.values():
                    if n["user"]["longName"] == selected_target:
                        target_id = n["num"]
            if target_id != -1:
                try:
                    iface.sendText(message, destinationId=target_id)
                    add_debug_line(f"{iface.getMyNodeInfo()['user']['shortName']}> {message}")
                    message_input_textbox.update("")
                except Exception as e:
                    sg.popup(f"Error sending message\n\n{e}", title="Error",
                             icon="meshtastic.ico")
            else:
                sg.popup(f"Cannot find target node with name '{selected_target}'", title="Error", icon="meshtastic.ico")

    elif (event == "Record") and not currently_recording:
        record_button.update(disabled=True)
        currently_recording = True
        with sr.Microphone() as source2:
            speech_recognizer.adjust_for_ambient_noise(source2, duration=0.2)

            try:
                audio = speech_recognizer.listen(source2)
                my_text = speech_recognizer.recognize_google(audio)
                message_input_textbox.update(my_text.lower())
            except Exception as e:
                sg.popup(f"Error recognising speech:\n\n{e}", title="Error", icon="meshtastic.ico")
            record_button.update(disabled=False)
        currently_recording = False

    if values["resolve_address_toggle"]:
        resolve_location_mode = True
    elif not values["resolve_address_toggle"]:
        resolve_location_mode = False

    if values["speech_to_text_toggle"] and not currently_recording:
        speech_to_text_mode = True
        record_button.update(disabled=False)
    if not values["speech_to_text_toggle"] and not currently_recording:
        speech_to_text_mode = False
        record_button.update(disabled=True)

    if values["text_to_speech_toggle"]:
        text_to_speech_mode = True
    elif not values["text_to_speech_toggle"]:
        text_to_speech_mode = False


main_window.close()

