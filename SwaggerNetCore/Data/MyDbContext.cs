using Microsoft.EntityFrameworkCore;
using SwaggerNetCore.Data.Models;

namespace SwaggerNetCore.Data
{
    public class MyDbContext : DbContext
    {
        public MyDbContext(DbContextOptions<MyDbContext> options) : base(options)
        {
        }

        public DbSet<TblCoefficients> TblCoefficients { get; set; }
        public DbSet<TblWebAppRequest> TblWebAppRequest { get; set; }
        public DbSet<TblWebAppRequestMaster> TblWebAppRequestMaster { get; set; }
    }
}
