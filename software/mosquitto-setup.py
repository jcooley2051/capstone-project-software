from subprocess import call

''' kill default mosquitto broker '''
call('sudo pkill mosquitto')

''' start new mosquitto broker with program config '''
call('mosquitto -c /etc/mosquitto/conf.d/port.conf')

''' subscribe to "readings" topic on port 1337 to receive sensor readings '''
call('mosquitto_sub -t readings -p 1337')