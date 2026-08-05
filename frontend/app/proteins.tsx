import { FoodGuideLayout } from "@/src/components/FoodGuideLayout";
import { api } from "@/src/lib/api";
import { useLang } from "@/src/lib/language-context";

export default function ProteinsGuideScreen() {
  const { t } = useLang();
  return (
    <FoodGuideLayout
      fetchGuide={api.getProteinGuide as any}
      title={t("proteinGuideTitle")}
      subtitle={t("proteinGuideSubtitle")}
      intro={t("proteinGuideIntro")}
      introIcon="egg"
      introTheme="brand"
      entriesKey="proteins"
      testIdPrefix="protein"
      backTestIdPrefix="proteins"
      errorLabel="Failed to load proteins guide"
    />
  );
}
