"use client";

import { useActionState } from "react";

import {
  runDueDailyBriefSchedule,
  updateDailyBriefScheduleWithState,
  type FormActionState,
} from "@/app/actions";
import type { DailyBriefSchedule } from "@/lib/api";


const WEEKDAYS = [
  [0, "Mon"],
  [1, "Tue"],
  [2, "Wed"],
  [3, "Thu"],
  [4, "Fri"],
  [5, "Sat"],
  [6, "Sun"],
] as const;

const TIMEZONES = ["UTC", "Asia/Kolkata", "America/New_York", "Europe/London"];
const INITIAL_STATE: FormActionState = { error: null };


export function DailyBriefScheduleForm({ schedule }: { schedule: DailyBriefSchedule | null }) {
  const [state, formAction, pending] = useActionState(
    updateDailyBriefScheduleWithState,
    INITIAL_STATE,
  );
  const selectedDays = new Set(schedule?.days_of_week ?? [0, 1, 2, 3, 4]);

  return (
    <div className="briefing-schedule-layout">
      <form action={formAction} className="briefing-schedule-form">
        <label className="briefing-schedule-toggle">
          <input name="enabled" type="checkbox" defaultChecked={schedule?.enabled ?? false} />
          <span>
            <strong>Enable local schedule</strong>
            <small>The worker generates a stored, rule-based brief without external AI.</small>
          </span>
        </label>
        <div className="briefing-schedule-fields">
          <label>
            <span>Local time</span>
            <input
              name="local_time"
              type="time"
              defaultValue={(schedule?.local_time || "07:00").slice(0, 5)}
              required
            />
          </label>
          <label>
            <span>Timezone</span>
            <select name="timezone" defaultValue={schedule?.timezone || "UTC"}>
              {TIMEZONES.map((timezone) => <option key={timezone}>{timezone}</option>)}
            </select>
          </label>
        </div>
        <fieldset className="briefing-schedule-days">
          <legend>Run on</legend>
          <div>
            {WEEKDAYS.map(([value, label]) => (
              <label key={value}>
                <input
                  name="days_of_week"
                  type="checkbox"
                  value={value}
                  defaultChecked={selectedDays.has(value)}
                />
                <span>{label}</span>
              </label>
            ))}
          </div>
        </fieldset>
        {state.error && <p className="form-error" role="alert">{state.error}</p>}
        <div className="button-row">
          <button type="submit" className="btn btn-primary" disabled={pending}>
            {pending ? "Saving schedule..." : "Save schedule"}
          </button>
        </div>
      </form>
      <aside className="briefing-schedule-status" aria-label="Daily Brief schedule status">
        <span className={`badge ${schedule?.enabled ? "badge-success" : "badge-outline"}`}>
          {schedule?.enabled ? "Enabled" : "Disabled"}
        </span>
        <dl>
          <div><dt>Next run</dt><dd>{schedule?.next_run_at ? new Date(schedule.next_run_at).toLocaleString() : "Not scheduled"}</dd></div>
          <div><dt>Last status</dt><dd>{schedule?.last_status?.replaceAll("_", " ") || "Never configured"}</dd></div>
          <div><dt>Last success</dt><dd>{schedule?.last_succeeded_at ? new Date(schedule.last_succeeded_at).toLocaleString() : "Never"}</dd></div>
          <div><dt>Generation</dt><dd>Rule-based, no external AI</dd></div>
        </dl>
        {schedule?.last_processing_run_id && (
          <a href="/data-health" className="text-link">Processing run #{schedule.last_processing_run_id}</a>
        )}
        <form action={runDueDailyBriefSchedule}>
          <button className="btn btn-secondary" type="submit" disabled={!schedule?.due_now}>
            {schedule?.due_now ? "Run due brief now" : "No brief is due"}
          </button>
        </form>
      </aside>
    </div>
  );
}
