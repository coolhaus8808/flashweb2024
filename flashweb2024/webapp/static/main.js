var socket = io.connect();

socket.on('connect', function () {
    console.log('Connected');
});

socket.on('response', function (data) {
    console.log('Received response:', data);
});

// egyéb üzenet küldése a szervernek
// socket.emit('message', {data: 'Data to send'});

// védett végpont hívása
// socket.emit('protected');
socket.on('protected_response', function (data) {
    console.log('Protected response:', data);
});
