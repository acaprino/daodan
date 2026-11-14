using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;

namespace Shop.Core;

public record Order(int Id, decimal Total);

public class ShopContext(DbContextOptions<ShopContext> options) : DbContext(options)
{
    public DbSet<Order> Orders => Set<Order>();
}

public static class ShopCoreServices
{
    public static IServiceCollection AddShopCore(this IServiceCollection services, string connectionString) =>
        services.AddDbContext<ShopContext>(options => options.UseNpgsql(connectionString));
}
