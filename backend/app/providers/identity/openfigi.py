"""OpenFIGI mapping returns candidates, never an automatic identity merge."""
from app.providers.market_data.parsing import fail
from app.providers.market_data.transport import AdapterTransport, provider_error
from app.schemas.data_adapters import IdentityCandidate, IdentityMappingRequest, IdentityMappingResult


class OpenFIGIProvider:
    provider_name = "openfigi"

    def __init__(self, api_key: str | None = None, *, transport=None):
        self.api_key = api_key
        self.transport = transport or AdapterTransport(self.provider_name)

    @property
    def captures(self):
        return self.transport.captures

    async def map_identity(self, request: IdentityMappingRequest) -> IdentityMappingResult:
        job = {"idType": request.id_type, "idValue": request.id_value,
               "includeUnlistedEquities": request.include_unlisted_equities}
        if request.exchange_code:
            job["exchCode"] = request.exchange_code.upper()
        if request.mic_code:
            job["micCode"] = request.mic_code.upper()
        response = await self.transport.request("https://api.openfigi.com/v3/mapping", payload=[job],
            headers={"X-OPENFIGI-APIKEY": self.api_key} if self.api_key else {})
        rows = response.payload
        if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
            fail(self.provider_name)
        item = rows[0]
        if item.get("error"):
            raise provider_error(self.provider_name, "PROVIDER_MAPPING_REJECTED", "OpenFIGI rejected the mapping request.", status=422)
        data = item.get("data", [])
        if not isinstance(data, list) or len(data) > 15000 or (not data and not item.get("warning")):
            fail(self.provider_name)
        candidates = []
        seen = set()
        for row in data:
            if not isinstance(row, dict) or not isinstance(row.get("figi"), str) or not row["figi"]:
                fail(self.provider_name)
            if row["figi"] in seen:
                continue
            seen.add(row["figi"])
            candidates.append(IdentityCandidate(figi=row["figi"], ticker=row.get("ticker"), name=row.get("name"),
                exchange_code=row.get("exchCode"), composite_figi=row.get("compositeFIGI"),
                share_class_figi=row.get("shareClassFIGI"), security_type=row.get("securityType"), market_sector=row.get("marketSector")))
        warnings = ["Mappings require review. No company, listing or share class is merged automatically.",
                    "This current lookup does not establish historical validity dates."]
        if not request.include_unlisted_equities:
            warnings.append("Unlisted equities were excluded by request; this is not a historical universe.")
        if item.get("warning"):
            warnings.append("OpenFIGI reported a mapping warning or no match.")
        return IdentityMappingResult(candidates=candidates, resolution="unresolved" if not candidates else
            "candidate" if len(candidates) == 1 else "ambiguous", observed_at=response.observed_at, warnings=warnings)
