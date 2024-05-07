using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;

namespace MySwaggerApi.Controllers
{
    [ApiController]
    [Route("[controller]")]
    public class ProductsController : ControllerBase
    {
        private static List<string> products = new List<string> { "Laptop", "Smartphone", "Tablet" };

        [HttpGet]
        public IEnumerable<string> Get()
        {
            return products;
        }

        [HttpPost]
        public IActionResult Post(string product)
        {
            products.Add(product);
            return CreatedAtAction(nameof(Get), new { id = products.Count - 1 });
        }

        [HttpDelete("{id}")]
        public IActionResult Delete(int id)
        {
            if (id < 0 || id >= products.Count)
            {
                return NotFound();
            }
            products.RemoveAt(id);
            return NoContent();
        }
    }
}
