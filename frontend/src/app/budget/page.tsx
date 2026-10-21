import { EventoraProvider } from "@/components/eventora-provider";
import { BudgetWorkspace } from "@/components/budget-workspace";

export default function BudgetPage() {
  return (
    <EventoraProvider>
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        <BudgetWorkspace />
      </div>
    </EventoraProvider>
  );
}
