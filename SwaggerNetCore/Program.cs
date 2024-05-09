using Microsoft.OpenApi.Models;
using Microsoft.EntityFrameworkCore;
using SwaggerNetCore.Data;


var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo { Title = "My API", Version = "v1" });
});

// Configure Entity Framework Core with MySQL
builder.Services.AddDbContext<MyDbContext>(options =>
    options.UseMySql(builder.Configuration.GetConnectionString("MySqlConnectionString"),
    ServerVersion.AutoDetect(builder.Configuration.GetConnectionString("MySqlConnectionString"))));

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseDeveloperExceptionPage();
    app.UseSwagger();
    app.UseSwaggerUI(c => c.SwaggerEndpoint("/swagger/v1/swagger.json", "My API V1"));
}

app.UseHttpsRedirection();
app.UseAuthorization();
app.MapControllers();

app.Run();
