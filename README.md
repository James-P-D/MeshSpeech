# MeshSpeech
Meshtastic desktop client with text-to/from-speech in Python

![Screenshot](https://github.com/James-P-D/MeshSpeech/blob/main/screenshot.gif)

## Introduction

I'm still pretty new to Lora/Meshtastic, so wanted to have a play with the Meshtastic-Python interface, and create a semi-useful app. To put it simply, this desktop app allows the user to connect to a Meshtastic device over a serial connection, and can then either type messages to send, or use the speech-to-text functionality for generating the message to send. When messages are received they are displayed, but can also be read back to the user. Finally, if the sending device provides GPS data, we can also resolve the sender's location.

## Requirements

Please consult the requirements.txt file for necessary libraries. 
