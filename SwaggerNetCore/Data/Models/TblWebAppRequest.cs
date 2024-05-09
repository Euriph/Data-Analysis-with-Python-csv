namespace SwaggerNetCore.Data.Models
{
    public class TblWebAppRequest
    {
        public int MasterUniqueId { get; set; }
        public DateTime DataDate { get; set; }
        public float DataValue { get; set; }

        public TblWebAppRequestMaster Master { get; set; }
    }
}
