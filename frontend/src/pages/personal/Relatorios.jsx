import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { FileText } from "lucide-react";
import ReportView from "../../components/ReportView";
import { EmptyState, ErrorState, PageHeader, SkeletonList } from "../../components/ui";
import { useFetch } from "../../lib/hooks";
import api from "../../services/api";

export default function Relatorios() {
  const [params] = useSearchParams();
  const [alunoId, setAlunoId] = useState(params.get("aluno") || "");
  const { data: alunos, loading, error, reload } = useFetch(async () => (await api.get("/users")).data, []);
  const current = alunoId || alunos?.[0]?.id || "";

  return (
    <>
      <PageHeader title="Relatórios" subtitle="Evolução por período, com PDF para compartilhar com o aluno."
        actions={alunos?.length > 0 && (
          <select className="input !w-auto" aria-label="Aluno" value={current} onChange={(e) => setAlunoId(e.target.value)}>
            {alunos.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
          </select>
        )} />
      {error && <ErrorState message={error} onRetry={reload} />}
      {loading && !alunos && <SkeletonList rows={3} />}
      {alunos && alunos.length === 0 && <EmptyState icon={FileText} title="Sem alunos para exibir" text="Quando você tiver alunos vinculados, os relatórios aparecem aqui." />}
      {current && <ReportView key={current} alunoId={Number(current)} canEdit />}
    </>
  );
}
