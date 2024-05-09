using System;

namespace SwaggerNetCore.Data.Models
{
    public class TblWebAppRequestMaster
    {
        public int UniqueId { get; set; }
        public DateTime TimeStamp { get; set; }
        public int RecordCount { get; set; }
        public string FileName { get; set; }
        public string UserName { get; set; }
    }
}
