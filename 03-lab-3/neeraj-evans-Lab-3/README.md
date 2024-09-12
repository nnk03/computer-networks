# Lab - 3 Solutions

## Submitted by

### Neeraj Krishna N - 112101033

### Evans Samuel Biju - 112101017

[Server and Client of A](./A) done by Neeraj
[Server and Client of B](./B) done by Evans

Run the following to make the files executable

```
chmod +x ./B/*
chmod +x ./A/*
```

by default server has `localhost` or `127.0.0.1` as its hostname

[This folder](./A) contains thread based client and asynchronous server

To Run, go to directory `A` and execute

```
./client_thread.py <hostname> <portNum>
./server_non_thread.py <portNum>
```

[This folder](./B) contains thread based server and asynchronous client

To Run, go to directory `B` and execute

```
./client_non_thread.py <hostname> <portNum>
./server_thread.py <portNum>
```
