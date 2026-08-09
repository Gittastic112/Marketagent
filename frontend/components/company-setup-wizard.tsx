"use client";

import { useState, useEffect } from "react";
import { useActionState } from "react";

import { createCompanyWithState, type FormActionState } from "@/app/actions";
import { CheckboxField, SelectField, TextField } from "@/components/form-fields";
import { lookupCompanyByTicker, fetchApiResponse } from "@/lib/api";

const initialState: FormActionState = { error: null };

export function CompanySetupWizard() {
  const [state, formAction, pending] = useActionState(createCompanyWithState, initialState);

  const [step, setStep] = useState(1);

  // Step 1 State
  const [market, setMarket] = useState("US");
  const [ticker, setTicker] = useState("");

  // Lookup/Metadata State
  const [lookupPending, setLookupPending] = useState(false);
  const [lookupMessage, setLookupMessage] = useState<string | null>(null);
  const [lookupError, setLookupError] = useState<string | null>(null);

  // Company Payload State
  const [exchange, setExchange] = useState("NASDAQ");
  const [localSymbol, setLocalSymbol] = useState("");
  const [name, setName] = useState("");
  const [cik, setCik] = useState("");
  const [isin, setIsin] = useState("");
  const [regulatoryId, setRegulatoryId] = useState("");
  const [regulatoryIdType, setRegulatoryIdType] = useState("CIK");
  const [country, setCountry] = useState("United States");
  const [currency, setCurrency] = useState("USD");
  const [damodaranIndustry, setDamodaranIndustry] = useState("");
  const [sector, setSector] = useState("");
  const [industry, setIndustry] = useState("");
  const [aliases, setAliases] = useState("");

  // Available Damodaran Industries
  const [availableIndustries, setAvailableIndustries] = useState<string[]>([]);
  const [industryPending, setIndustryPending] = useState(false);
  const [industryError, setIndustryError] = useState<string | null>(null);
  const [industryWarnings, setIndustryWarnings] = useState<string[]>([]);

  useEffect(() => {
    if (step !== 4) {
      return;
    }

    let cancelled = false;
    setIndustryPending(true);
    setIndustryError(null);
    setIndustryWarnings([]);
    void fetchApiResponse<string[]>(`/industries/candidates?country=${encodeURIComponent(country)}`)
      .then((response) => {
        if (cancelled) return;
        const industries = response.data ?? [];
        setAvailableIndustries(industries);
        setIndustryWarnings(response.meta?.warnings ?? []);
        if (response.errors?.length) {
          setIndustryError(response.errors[0].message);
        } else if (industries.length === 0) {
          setIndustryError("No Damodaran industry taxonomy is loaded. Import benchmark data before creating the company.");
        }
      })
      .catch((error) => {
        if (cancelled) return;
        setAvailableIndustries([]);
        setIndustryError(error instanceof Error ? error.message : "Could not load Damodaran industries.");
      })
      .finally(() => {
        if (!cancelled) setIndustryPending(false);
      });

    return () => {
      cancelled = true;
    };
  }, [step, country]);

  function applyMarketDefaults(nextMarket: string) {
    setMarket(nextMarket);
    setExchange(nextMarket === "IN" ? "NSE" : "NASDAQ");
    setCountry(nextMarket === "IN" ? "India" : "United States");
    setCurrency(nextMarket === "IN" ? "INR" : "USD");
    setRegulatoryIdType(nextMarket === "IN" ? "ISIN" : "CIK");
    setCik("");
    setIsin("");
    setRegulatoryId("");
    setLookupMessage(null);
    setLookupError(null);
  }

  async function handleLookup() {
    const normalizedTicker = ticker.trim().toUpperCase();
    if (!normalizedTicker || lookupPending) return;

    setLookupPending(true);
    setLookupMessage(null);
    setLookupError(null);
    try {
      const result = await lookupCompanyByTicker(normalizedTicker, { market, exchange });
      setTicker(result.ticker);
      setLocalSymbol(result.local_symbol ?? result.ticker);
      setName(result.name);
      setCountry(result.country ?? country);
      setCurrency(result.currency ?? currency);
      setIsin(result.isin ?? "");
      setRegulatoryId(result.regulatory_id ?? result.cik ?? "");
      setRegulatoryIdType(result.regulatory_id_type ?? (market === "IN" ? "ISIN" : "CIK"));
      setCik(result.cik ?? (result.regulatory_id_type === "CIK" ? result.regulatory_id ?? "" : ""));
      setSector(result.sector ?? "");
      setIndustry(result.industry ?? "");
      setExchange(result.primary_exchange ?? exchange);

      setLookupMessage(`Successfully found: ${result.name}`);
      setTimeout(() => setStep(3), 1000); // Auto-advance on success
    } catch (error) {
      setLookupError(error instanceof Error ? error.message : "Ticker lookup failed.");
    } finally {
      setLookupPending(false);
    }
  }

  function renderStepIndicator() {
    const steps = ["Identity", "Lookup", "Fundamentals", "Industry", "Review"];
    return (
      <div style={{ display: "flex", gap: "10px", marginBottom: "2rem", justifyContent: "space-between" }}>
        {steps.map((s, idx) => (
          <div key={s} style={{
            flex: 1,
            padding: "8px",
            borderBottom: step >= idx + 1 ? "2px solid var(--text-primary)" : "2px solid var(--border)",
            color: step >= idx + 1 ? "var(--text-primary)" : "var(--muted)",
            fontSize: "0.85rem",
            fontWeight: step >= idx + 1 ? 600 : 400
          }}>
            {idx + 1}. {s}
          </div>
        ))}
      </div>
    );
  }

  return (
    <div style={{ maxWidth: "600px" }}>
      <h2>Company Setup Wizard</h2>
      <p style={{ color: "var(--text-secondary)", marginBottom: "2rem" }}>
        Guided setup to ensure consistent identity, currency, and industry mapping.
      </p>

      {renderStepIndicator()}

      <form action={formAction} className="form-grid">
        {state.error && (
          <div className="field-full error" role="alert">
            {state.error}
          </div>
        )}

        {/* Hidden inputs to pass data to server action */}
        <input type="hidden" name="market" value={market} />
        <input type="hidden" name="ticker" value={ticker} />
        <input type="hidden" name="primary_exchange" value={exchange} />
        <input type="hidden" name="exchange" value={exchange} />
        <input type="hidden" name="local_symbol" value={localSymbol || ticker} />
        <input type="hidden" name="name" value={name} />
        <input type="hidden" name="country" value={country} />
        <input type="hidden" name="currency" value={currency} />
        <input type="hidden" name="damodaran_industry" value={damodaranIndustry} />
        <input type="hidden" name="sector" value={sector} />
        <input type="hidden" name="industry" value={industry} />
        <input type="hidden" name="isin" value={isin} />
        <input type="hidden" name="cik" value={cik} />
        <input type="hidden" name="regulatory_id" value={regulatoryId} />
        <input type="hidden" name="regulatory_id_type" value={regulatoryIdType} />
        <input type="hidden" name="aliases" value={aliases} />
        <input type="hidden" name="active" value="on" />

        {/* Step 1: Market & Ticker */}
        {step === 1 && (
          <div className="field-full" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <h3>Step 1: Market & Ticker</h3>
            <div style={{ display: "flex", gap: "1rem" }}>
              <SelectField id="market" label="Market" name="_market" onChange={(e) => applyMarketDefaults(e.target.value)} value={market}>
                <option value="US">United States (US)</option>
                <option value="IN">India (IN)</option>
              </SelectField>
              <TextField
                id="ticker"
                label="Ticker"
                name="_ticker"
                onChange={(e) => {
                  const val = e.target.value.toUpperCase();
                  setTicker(val);
                  setLocalSymbol(val);
                }}
                required
                value={ticker}
                placeholder="e.g. AAPL"
              />
            </div>
            <div className="button-row" style={{ marginTop: "1rem" }}>
              <button type="button" onClick={() => setStep(2)} disabled={!ticker}>Next Step</button>
            </div>
          </div>
        )}

        {/* Step 2: Metadata Lookup */}
        {step === 2 && (
          <div className="field-full" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <h3>Step 2: Metadata Lookup</h3>
            <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)" }}>
              We will query SEC/OpenFIGI for <strong>{ticker}</strong> on the <strong>{market}</strong> market.
            </p>
            {lookupError && <div className="error">{lookupError}</div>}
            {lookupMessage && <div className="success-message">{lookupMessage}</div>}

            {!lookupMessage && (
              <div className="button-row">
                <button type="button" className="secondary-button" onClick={() => setStep(1)}>Back</button>
                <button type="button" onClick={() => void handleLookup()} disabled={lookupPending}>
                  {lookupPending ? "Looking up..." : "Lookup Metadata"}
                </button>
                <button type="button" className="secondary-button" onClick={() => setStep(3)}>Skip Lookup</button>
              </div>
            )}
          </div>
        )}

        {/* Step 3: Fundamentals Mapping */}
        {step === 3 && (
          <div className="field-full" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <h3>Step 3: Company Details & Fundamentals</h3>
            <TextField id="name" label="Company Name" name="_name" onChange={(e) => setName(e.target.value)} required value={name} />
            <div style={{ display: "flex", gap: "1rem" }}>
              <TextField id="country" label="Country" name="_country" onChange={(e) => setCountry(e.target.value)} required value={country} />
              <TextField id="currency" label="Currency" name="_currency" onChange={(e) => setCurrency(e.target.value.toUpperCase())} required value={currency} />
            </div>
            <div style={{ display: "flex", gap: "1rem" }}>
              <TextField id="exchange" label="Exchange" name="_exchange" onChange={(e) => setExchange(e.target.value.toUpperCase())} value={exchange} />
              <TextField id="local_symbol" label="Local Symbol" name="_local_symbol" onChange={(e) => setLocalSymbol(e.target.value.toUpperCase())} required value={localSymbol} />
            </div>
            <div className="button-row" style={{ marginTop: "1rem" }}>
              <button type="button" className="secondary-button" onClick={() => setStep(2)}>Back</button>
              <button type="button" onClick={() => setStep(4)} disabled={!name || !country || !currency}>Next Step</button>
            </div>
          </div>
        )}

        {/* Step 4: Damodaran Industry Mapping */}
        {step === 4 && (
          <div className="field-full" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <h3>Step 4: Damodaran Industry Mapping</h3>
            <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)" }}>
              Select a Damodaran industry to link benchmarking data (cost of capital, margins, etc).
            </p>
            {sector && <p style={{ fontSize: "0.85rem", margin: 0 }}><strong>Lookup Sector:</strong> {sector}</p>}
            {industry && <p style={{ fontSize: "0.85rem", margin: 0 }}><strong>Lookup Industry:</strong> {industry}</p>}
            {industryPending && <p className="muted">Loading industry taxonomy...</p>}
            {industryWarnings.map((warning) => (
              <p className="muted" key={warning}>{warning}</p>
            ))}
            {industryError && (
              <div className="error" role="alert">
                {industryError} <a href="/admin/damodaran">Open Damodaran imports</a>
              </div>
            )}

            <SelectField
              id="damodaran_industry"
              label="Damodaran Industry"
              name="_damodaran_industry"
              onChange={(e) => setDamodaranIndustry(e.target.value)}
              value={damodaranIndustry}
              disabled={industryPending || availableIndustries.length === 0}
              required
            >
              <option value="">-- Select Industry --</option>
              {availableIndustries.map(ind => (
                <option key={ind} value={ind}>{ind}</option>
              ))}
            </SelectField>

            <div className="button-row" style={{ marginTop: "1rem" }}>
              <button type="button" className="secondary-button" onClick={() => setStep(3)}>Back</button>
              <button type="button" onClick={() => setStep(5)} disabled={!damodaranIndustry}>Next Step</button>
            </div>
          </div>
        )}

        {/* Step 5: Review & Create */}
        {step === 5 && (
          <div className="field-full" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <h3>Step 5: Review & Create</h3>
            <div style={{ background: "var(--surface)", padding: "1rem", borderRadius: "8px", border: "1px solid var(--border)" }}>
              <dl style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "0.5rem", margin: 0, fontSize: "0.9rem" }}>
                <dt style={{ color: "var(--muted)" }}>Name:</dt><dd style={{ margin: 0 }}><strong>{name}</strong></dd>
                <dt style={{ color: "var(--muted)" }}>Ticker:</dt><dd style={{ margin: 0 }}>{ticker} ({exchange})</dd>
                <dt style={{ color: "var(--muted)" }}>Market:</dt><dd style={{ margin: 0 }}>{market}</dd>
                <dt style={{ color: "var(--muted)" }}>Currency:</dt><dd style={{ margin: 0 }}>{currency}</dd>
                <dt style={{ color: "var(--muted)" }}>Country:</dt><dd style={{ margin: 0 }}>{country}</dd>
                <dt style={{ color: "var(--muted)" }}>Industry:</dt><dd style={{ margin: 0, color: "var(--success-color, #4CAF50)" }}>{damodaranIndustry}</dd>
                {cik && <><dt style={{ color: "var(--muted)" }}>CIK:</dt><dd style={{ margin: 0 }}>{cik}</dd></>}
                {isin && <><dt style={{ color: "var(--muted)" }}>ISIN:</dt><dd style={{ margin: 0 }}>{isin}</dd></>}
              </dl>
            </div>
            <div className="button-row" style={{ marginTop: "1rem" }}>
              <button type="button" className="secondary-button" onClick={() => setStep(4)}>Back</button>
              <button type="submit" disabled={pending}>
                {pending ? "Creating..." : "Create Company"}
              </button>
            </div>
          </div>
        )}
      </form>
    </div>
  );
}
