using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Http;
using System.Diagnostics;
using SwaggerNetCore.Data;
using SwaggerNetCore.Data.Models;
using System.IO;
using System.Threading.Tasks;
using System.Net.Http;
using System.Net.Http.Headers;


namespace SwaggerNetCore.Controllers
{
    [ApiController]
    [Route("[controller]")]
    public class DataController : ControllerBase
    {
        private readonly MyDbContext _context;

        public DataController(MyDbContext context)
        {
            _context = context;
        }

        [HttpPost("upload")]
        public async Task<IActionResult> UploadFile(IFormFile file)
        {
            if (file == null || file.Length == 0)
                return BadRequest("No file uploaded.");

            var path = Path.GetTempFileName();

            using (var stream = new FileStream(path, FileMode.Create))
            {
                await file.CopyToAsync(stream);
            }

            // Run the Python script
            var result = RunPythonScript(path);

            // Save result to database
            _context.TblCoefficients.Add(new TblCoefficients { B0 = result.B0, B1 = result.B1, ProcessDate = DateTime.Now });
            await _context.SaveChangesAsync();

            return Ok(new { b0 = result.B0, b1 = result.B1 });
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





        private (float B0, float B1) RunPythonScript(string path)
        {
            ProcessStartInfo start = new ProcessStartInfo();
            start.FileName = "python"; // Specify exe name.
            start.Arguments = $"path_to_script.py {path}"; // Specify arguments.
            start.UseShellExecute = false;
            start.RedirectStandardOutput = true;
            start.RedirectStandardError = true;

            using (Process process = Process.Start(start))
            {
                using (StreamReader reader = process.StandardOutput)
                {
                    string result = reader.ReadToEnd();
                    // Parse result assuming it's in the form 'b0, b1'
                    var results = result.Split(',');
                    float b0 = float.Parse(results[0]);
                    float b1 = float.Parse(results[1]);
                    return (b0, b1);
                }
            }
        }
    }
}
