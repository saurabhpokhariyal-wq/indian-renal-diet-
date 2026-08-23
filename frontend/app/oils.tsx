import { FoodGuideLayout } from "@/src/components/FoodGuideLayout";
import { api } from "@/src/lib/api";
import { useLang } from "@/src/lib/language-context";

export default function OilsGuideScreen() {
  const { t } = useLang();
  return (
    <FoodGuideLayout
      fetchGuide={api.getOilGuide as any}
      title={t("oilGuideTitle")}
      subtitle={t("oilGuideSubtitle")}
      intro={t("oilGuideIntro")}
      introIcon="water-outline"
      introTheme="brand"
      entriesKey="oils"
      testIdPrefix="oil"
      backTestIdPrefix="oils"
      errorLabel="Failed to load oils guide"
    />
  );
}
