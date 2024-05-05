var socket = io.connect();

socket.on('connect', function () {
    console.log('Connected');
});

socket.on('response', function (data) {
    console.log('Received response:', data);
});

// egy�b �zenet k�ld�se a szervernek
// socket.emit('message', {data: 'Data to send'});

// v�dett v�gpont h�v�sa
// socket.emit('protected');
socket.on('protected_response', function (data) {
    console.log('Protected response:', data);
});
