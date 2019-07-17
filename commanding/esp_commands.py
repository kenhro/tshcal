from newportESP import ESP
from time import sleep


esp = ESP('/dev/ttyUSB0')  # open communication with controller
stage = esp.axis(1)        # open axis no 1
print(stage.id)
stage.on()
print(stage.position)# print stage ID
stage.move_by(-5, True)
sleep(10)# Move to position 1.2 mm
print(stage.position)
stage.move_by(5, True)
print(stage.position)# print stage ID