using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Http;
using System.Diagnostics;
using SwaggerNetCore.Data;
using SwaggerNetCore.Data.Models;
using System.IO;
using System.Threading.Tasks;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;


namespace SwaggerNetCore.Controllers
{
    [ApiController]
    [Route("[controller]")]
    public class DataController : ControllerBase
    {

        // Define the DTO class
        public class DataItemDTO
        {
            public string Date { get; set; }   // Date in string format
            public double Value { get; set; }
            public string Username { get; set; } // Adjust to 'Username' to match Flask's expected field
        }

        [HttpPost("submit-single-data")]
        public async Task<IActionResult> SubmitSingleData([FromBody] DataItemDTO dataItem)
        {
            using (var httpClient = new HttpClient())
            {
                // Ensure JSON is serialized with the correct property names
                var jsonContent = JsonSerializer.Serialize(dataItem, new JsonSerializerOptions
                {
                    PropertyNamingPolicy = JsonNamingPolicy.CamelCase
                });
                var content = new StringContent(jsonContent, Encoding.UTF8, "application/json");

                // Adjust the URL to match your Flask route
                var response = await httpClient.PostAsync("http://localhost:5000/submit_single_data", content);
                if (response.IsSuccessStatusCode)
                {
                    var responseData = await response.Content.ReadAsStringAsync();
                    return Ok(responseData);
                }
                else
                {
                    // Extract more detailed error information if available
                    var errorResponse = await response.Content.ReadAsStringAsync();
                    return BadRequest($"Failed to post data to Flask server. Server response: {errorResponse}");
                }
            }
        }

        [HttpPost("upload-csv")]
        public async Task<IActionResult> UploadCsv(IFormFile file)
        {
            if (file == null || file.Length == 0)
            {
                return BadRequest("No file uploaded.");
            }

            using (var httpClient = new HttpClient())
            {
                using (var form = new MultipartFormDataContent())
                {
                    using (var fileStream = file.OpenReadStream())
                    {
                        using (var content = new StreamContent(fileStream))
                        {
                            content.Headers.ContentDisposition = new ContentDispositionHeaderValue("form-data")
                            {
                                Name = "file",
                                FileName = file.FileName
                            };
                            form.Add(content);

                            var response = await httpClient.PostAsync("http://localhost:5000/upload_csv", form);
                            if (response.IsSuccessStatusCode)
                            {
                                var responseData = await response.Content.ReadAsStringAsync();
                                return Ok(responseData);
                            }
                            else
                            {
                                return BadRequest("Failed to upload to Flask server.");
                            }
                        }
                    }
                }
            }
        }

    }
}
