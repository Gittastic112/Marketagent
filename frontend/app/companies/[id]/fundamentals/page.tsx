import { notFound } from "next/navigation";
import Link from "next/link";
import { fetchApi, Company, listFinancialPeriods } from "@/lib/api";
import { deleteFinancialStatementPeriod } from "@/app/actions";

export default async function FundamentalsPage(props: { params: Promise<{ id: string }> }) {
  const params = await props.params;
  const companyId = parseInt(params.id, 10);
  if (isNaN(companyId)) {
    notFound();
  }

  let company: Company;
  try {
    company = await fetchApi<Company>(`/companies/${companyId}`);
  } catch {
    notFound();
  }

  const periods = await listFinancialPeriods(companyId);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Fundamentals: {company.ticker}</h1>
          <p className="text-muted-foreground">{company.name}</p>
        </div>
        <Link
          href={`/companies/${company.id}`}
          className="text-sm font-medium text-blue-600 hover:text-blue-500"
        >
          &larr; Back to Dashboard
        </Link>
      </div>

      <div className="bg-white shadow sm:rounded-lg overflow-hidden">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-base font-semibold leading-6 text-gray-900">Financial Periods</h3>
          <div className="mt-4 flow-root">
            <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
              <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
                {periods.length === 0 ? (
                  <p className="text-sm text-gray-500">No financial periods found. (API ingestion needed)</p>
                ) : (
                  <table className="min-w-full divide-y divide-gray-300">
                    <thead>
                      <tr>
                        <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900">Period</th>
                        <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Year</th>
                        <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Quarter</th>
                        <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Report Date</th>
                        <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Currency</th>
                        <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Metrics</th>
                        <th scope="col" className="relative py-3.5 pl-3 pr-4 sm:pr-0">
                          <span className="sr-only">Delete</span>
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {periods.map((period) => (
                        <tr key={period.id}>
                          <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900">{period.period_type}</td>
                          <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">{period.year}</td>
                          <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">{period.quarter ?? "-"}</td>
                          <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">{period.report_date}</td>
                          <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">{period.currency}</td>
                          <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                            {period.metrics.length} metrics
                          </td>
                          <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-0">
                            <form action={async (data) => {
                              "use server";
                              await deleteFinancialStatementPeriod(data, companyId.toString());
                            }}>
                              <input type="hidden" name="id" value={period.id} />
                              <button type="submit" className="text-red-600 hover:text-red-900">
                                Delete
                              </button>
                            </form>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
