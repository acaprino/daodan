package com.example.greeting;

import com.example.greeting.v1.HelloReply;
import com.example.greeting.v1.HelloRequest;

public final class Greeter {
    public HelloReply greet(HelloRequest request) {
        return HelloReply.newBuilder().setMessage("Hello, " + request.getName()).build();
    }
}
