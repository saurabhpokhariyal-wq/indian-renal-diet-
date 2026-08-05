import { FoodGuideLayout } from "@/src/components/FoodGuideLayout";
import { api } from "@/src/lib/api";
import { useLang } from "@/src/lib/language-context";

export default function VegetablesGuideScreen() {
  const { t } = useLang();
  return (
    <FoodGuideLayout
      fetchGuide={api.getVegetableGuide as any}
      title={t("vegetableGuideTitle")}
      subtitle={t("vegetableGuideSubtitle")}
      intro={t("vegetableGuideIntro")}
      introIcon="leaf"
      introTheme="brand"
      entriesKey="vegetables"
      testIdPrefix="vegetable"
      backTestIdPrefix="vegetables"
      errorLabel="Failed to load vegetable guide"
    />
  );
}
