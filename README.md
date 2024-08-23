# TeleFeedback
Leave or listen to feedback using a phone.

3. Install Dependencies:
```
sudo apt-get install sox libsox-fmt-mp3
```

# Automated start and restart
1. Copy the .service file to the systemd system directory:
```
sudo cp telefeedback.service /etc/systemd/system/
```
2. Reload the systemd daemon to recognize the new service file:
```
sudo systemctl daemon-reload
```
3. Enable and start the service to start on boot:
```
sudo systemctl enable telefeedback.service
sudo systemctl start telefeedback.service
```
4. Check the status of the service to ensure it's running:
```
sudo systemctl status telefeedback.service
```
5. Restart the system
```
sudo reboot
```


# Video Demo
<a href="http://www.youtube.com/watch?feature=player_embedded&v=lMZIa6t9k3g" target="_blank"><img src="http://img.youtube.com/vi/lMZIa6t9k3g/0.jpg" 
alt="Youtube Link" width="240" height="180" border="10" /></a>
