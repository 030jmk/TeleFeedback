#! /usr/bin/python3

import os
import subprocess
import RPi.GPIO as GPIO
from time import sleep
import datetime
import random
import time

# Pin definitions
pulse_input_pin = 2
reset_button_pin = 3
switch_hook_pin = 26

# Initialize process variable
process = None
exp_started = False
pulse_count = 0
reset_button_pressed = False
recording_process = None
reset_button_hold_time = 0
reset_button_hold_threshold = 2  # 2 seconds hold time

audio_folder = "recordings"
audio_files = [f for f in os.listdir(audio_folder) if f.endswith('.wav') or f.endswith('.mp3')]
last_played = None

def random_audio():
    global last_played
    if len(audio_files) > 1:
        available_files = [f for f in audio_files if f != last_played]
        random_file = random.choice(available_files)
    elif audio_files:
        random_file = audio_files[0]
    else:
        return None
    
    last_played = random_file
    full_path = os.path.join(audio_folder, random_file)
    return full_path

class ResetPressedException(Exception):
    print("Starting")
    sleep(1)
    pass

def pulse_detected(channel):
    global pulse_count
    pulse_count += 1

def reset_pulse_helper():
    global pulse_count
    sleep(5)  # Replace with the number of seconds you want to count pulses for
    print(f"Number dialed: {pulse_count}")
    return pulse_count

def reset_callback(channel):
    if not GPIO.input(reset_button_pin):
        raise ResetPressedException("reset is pressed")

def reset_button_callback(channel):
    global reset_button_pressed, reset_button_hold_time
    if not GPIO.input(reset_button_pin):
        reset_button_hold_time = time.time()
    else:
        if time.time() - reset_button_hold_time >= reset_button_hold_threshold:
            reset_button_pressed = True
        reset_button_hold_time = 0

def current_datetime():
    current_time = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    return current_time

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(reset_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(pulse_input_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(switch_hook_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(reset_button_pin, GPIO.BOTH, callback=reset_button_callback, bouncetime=300)
GPIO.add_event_detect(pulse_input_pin, GPIO.FALLING, callback=pulse_detected, bouncetime=100)
GPIO.add_event_detect(switch_hook_pin, GPIO.BOTH, callback=lambda _: None, bouncetime=200)

def record_audio(filename, max_duration=60):
    os.makedirs("recordings", exist_ok=True)
    output_path = os.path.join("recordings", filename)
    command = ["rec", "-q", output_path, "trim", "0", str(max_duration)]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process

def stop_recording(process):
    if process and process.poll() is None:
        process.terminate()
        process.wait()
        print("Recording stopped.")
    else:
        print("Recording had already finished.")

def play_interruptible(audio_file, channel):
    process = subprocess.Popen(["play", "-q", audio_file, "-t", "alsa"])
    while process.poll() is None:
        if GPIO.input(channel) == 0:
            process.terminate()
            process.wait()
            return False
        sleep(0.1)
    return True

def exp_start(channel):
    global process, exp_started, pulse_count, recording_process, reset_button_pressed

    if channel == switch_hook_pin and not exp_started:
        print(current_datetime())
        
        if reset_button_pressed:
            # Alternative experience: play random recordings
            play_interruptible("intro_recordings.mp3", channel)
            while GPIO.input(channel) == 1:  # While phone is off hook
                sleep(1)
                audio_file = random_audio()
                if audio_file:
                    if not play_interruptible(audio_file, channel):
                        break
                sleep(1)
            reset_button_pressed = False
            return  # Exit the function to restart the normal experience

        # Normal experience starts here
        if not play_interruptible("dual_tone.wav", channel):
            return

        if not play_interruptible("introduction.mp3", channel):
            return

        sleep(1)
        if not play_interruptible("beep.wav", channel):
            return

        # Start recording
        filename = f"recording_{current_datetime()}.wav"
        recording_process = record_audio(filename)

        # Wait for the recording to finish or for the switch hook to be pressed
        start_time = datetime.datetime.now()
        while (datetime.datetime.now() - start_time).total_seconds() < 60 and GPIO.input(channel) == 1:
            sleep(0.1)

        # Stop the recording
        stop_recording(recording_process)
        if GPIO.input(channel) == 0:
            return

        if not play_interruptible("Gassenbesetztton.wav", channel):
            return

        if GPIO.input(channel) == 0:
            return
        sleep(1)

        if not play_interruptible("Gassenbesetztton.wav", channel):
            return

        if GPIO.input(channel) == 0:
            return
        sleep(1)

        while GPIO.input(channel) == 1:
            sleep(2)
            continue

def exp_stop(channel):
    global process, exp_started, recording_process
    if channel == switch_hook_pin:
        if recording_process:
            stop_recording(recording_process)
        process = None
        exp_started = False

def main_loop():
    global process, exp_started
    try:
        while True:
            if GPIO.input(switch_hook_pin) == False and exp_started == False:
                sleep(2)
            else:
                print("switch hook un-pressed")
                exp_start(switch_hook_pin)

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Restarting...")
        process = None
        exp_started = False
        pulse_count = 0
        reset_button_pressed = False
        if process is not None:
            exp_stop(switch_hook_pin)
            print("experience stopped..")
        print("starting main_loop again.")
        main_loop()

if __name__ == '__main__':
    try:
        main_loop()
    except KeyboardInterrupt:
        print("Exiting gracefully")
        GPIO.cleanup()
    except Exception as e:
        print(f"Error in main loop: {e}")
