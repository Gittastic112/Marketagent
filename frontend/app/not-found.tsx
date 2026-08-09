import { ArrowLeft, Building2 } from "lucide-react";
import Link from "next/link";


export default function NotFound() {
  return (
    <section className="route-state">
      <p className="eyebrow">Not found</p>
      <h1>The requested workspace does not exist</h1>
      <div className="button-row">
        <Link href="/" className="secondary-button">
          <ArrowLeft size={16} />
          Dashboard
        </Link>
        <Link href="/companies" className="secondary-button">
          <Building2 size={16} />
          Companies
        </Link>
      </div>
    </section>
  );
}
