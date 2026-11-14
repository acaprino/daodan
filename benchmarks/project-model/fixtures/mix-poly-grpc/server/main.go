package main

import (
	"context"
	"log"
	"net"

	shopv1 "github.com/acme/shop/server/gen/shop/v1"
	"google.golang.org/grpc"
)

type orders struct {
	shopv1.UnimplementedOrderServiceServer
}

func (orders) GetOrder(_ context.Context, req *shopv1.GetOrderRequest) (*shopv1.GetOrderResponse, error) {
	return &shopv1.GetOrderResponse{Id: req.GetId(), TotalCents: 1250}, nil
}

func main() {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatal(err)
	}
	s := grpc.NewServer()
	shopv1.RegisterOrderServiceServer(s, orders{})
	log.Fatal(s.Serve(lis))
}
