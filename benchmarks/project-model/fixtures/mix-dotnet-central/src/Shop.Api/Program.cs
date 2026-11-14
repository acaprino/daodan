using Serilog;
using Shop.Core;

var builder = WebApplication.CreateBuilder(args);
builder.Host.UseSerilog((context, config) => config.WriteTo.Console());
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
builder.Services.AddShopCore(builder.Configuration.GetConnectionString("Shop")!);

var app = builder.Build();
app.UseSwagger();
app.MapGet("/orders/{id:int}", (int id) => new Order(id, 0m));
app.Run();
