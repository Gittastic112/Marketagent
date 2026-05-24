import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { fetchApi } from "@/lib/api";
import type { AlertRecord } from "@/lib/api";

export default async function AlertsPage() {
  try {
    const alerts = await fetchApi<AlertRecord[]>("/alerts");

    return (
      <>
        <PageHeader eyebrow="Review queue" title="Alerts" status={`${alerts.length} alerts`} />
        <Panel title="Alerts">
          {alerts.length === 0 ? (
            <EmptyState label="No alerts yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Type</th>
                    <th>Severity</th>
                    <th>Confidence</th>
                    <th>Review</th>
                  </tr>
                </thead>
                <tbody>
                  {alerts.map((alert) => (
                    <tr key={alert.id}>
                      <td>{alert.title}</td>
                      <td>{alert.alert_type}</td>
                      <td>{alert.severity}</td>
                      <td>{alert.confidence_bucket}</td>
                      <td>
                        <span className="badge">{alert.review_status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      </>
    );
  } catch {
    return (
      <>
        <PageHeader eyebrow="Review queue" title="Alerts" />
        <ErrorState message="Could not load alerts from the backend API." />
      </>
    );
  }
}
