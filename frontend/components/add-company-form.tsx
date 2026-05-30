"use client";

import { useState } from "react";
import { useActionState } from "react";

import { createCompanyWithState, type FormActionState } from "@/app/actions";
import { CheckboxField, SelectField, TextField } from "@/components/form-fields";
import { lookupCompanyByTicker } from "@/lib/api";

const initialState: FormActionState = { error: null };

export function AddCompanyForm() {
  const [state, formAction, pending] = useActionState(createCompanyWithState, initialState);
  const [ticker, setTicker] = useState("");
  const [name, setName] = useState("");
  const [cik, setCik] = useState("");
  const [lookupPending, setLookupPending] = useState(false);
  const [lookupMessage, setLookupMessage] = useState<string | null>(null);
  const [lookupError, setLookupError] = useState<string | null>(null);

  async function lookupTicker() {
    const normalizedTicker = ticker.trim().toUpperCase();
    if (!normalizedTicker || lookupPending) {
      return;
    }
    setLookupPending(true);
    setLookupMessage(null);
    setLookupError(null);
    try {
      const result = await lookupCompanyByTicker(normalizedTicker);
      setTicker(result.ticker);
      setName(result.name);
      setCik(result.cik);
      setLookupMessage(`Found ${result.name}`);
    } catch (error) {
      setLookupError(error instanceof Error ? error.message : "Ticker lookup failed.");
    } finally {
      setLookupPending(false);
    }
  }

  return (
    <form action={formAction} className="form-grid">
      {state.error ? (
        <div className="field-full error" role="alert">
          {state.error}
        </div>
      ) : null}
      {lookupError ? (
        <div className="field-full error" role="alert">
          {lookupError}
        </div>
      ) : null}
      {lookupMessage ? <div className="field-full success-message">{lookupMessage}</div> : null}
      <div className="field lookup-field">
        <label htmlFor="ticker">Ticker</label>
        <input
          id="ticker"
          name="ticker"
          onBlur={() => {
            if (ticker && !name) {
              void lookupTicker();
            }
          }}
          onChange={(event) => {
            setTicker(event.target.value.toUpperCase());
            setLookupMessage(null);
            setLookupError(null);
          }}
          required
          value={ticker}
        />
        <button className="secondary-button" disabled={lookupPending || !ticker.trim()} onClick={() => void lookupTicker()} type="button">
          {lookupPending ? "Looking..." : "Lookup"}
        </button>
      </div>
      <TextField className="field field-wide" id="name" label="Name" name="name" onChange={(event) => setName(event.target.value)} required value={name} />
      <TextField id="exchange" label="Exchange" name="exchange" placeholder="NASDAQ" />
      <TextField id="sector" label="Sector" name="sector" />
      <TextField id="industry" label="Industry" name="industry" />
      <TextField id="country" label="Country" name="country" />
      <TextField id="region" label="Region" name="region" />
      <TextField id="currency" label="Currency" name="currency" placeholder="USD" />
      <SelectField id="asset_type" label="Asset Type" name="asset_type">
        <option value="">Select type</option>
        <option value="equity">equity</option>
        <option value="etf">etf</option>
        <option value="fund">fund</option>
        <option value="cash">cash</option>
        <option value="crypto">crypto</option>
        <option value="other">other</option>
      </SelectField>
      <SelectField id="security_type" label="Security Type" name="security_type">
        <option value="">Select type</option>
        <option value="common_stock">common_stock</option>
        <option value="adr">adr</option>
        <option value="etf">etf</option>
        <option value="mutual_fund">mutual_fund</option>
        <option value="preferred_stock">preferred_stock</option>
        <option value="other">other</option>
      </SelectField>
      <SelectField id="market_cap_category" label="Market Cap" name="market_cap_category">
        <option value="">Select cap</option>
        <option value="mega_cap">mega_cap</option>
        <option value="large_cap">large_cap</option>
        <option value="mid_cap">mid_cap</option>
        <option value="small_cap">small_cap</option>
        <option value="micro_cap">micro_cap</option>
        <option value="unknown">unknown</option>
      </SelectField>
      <TextField id="cik" label="CIK" name="cik" onChange={(event) => setCik(event.target.value)} value={cik} />
      <TextField className="field field-wide" id="aliases" label="Aliases" name="aliases" placeholder="Google, Facebook" />
      <TextField id="etf_provider" label="ETF Provider" name="etf_provider" />
      <CheckboxField checkboxLabel="ETF" id="is_etf" label="ETF" name="is_etf" />
      <CheckboxField checkboxLabel="Active" defaultChecked id="active" label="Status" name="active" />
      <div className="button-row">
        <button disabled={pending} type="submit">
          {pending ? "Adding..." : "Add company"}
        </button>
      </div>
    </form>
  );
}
