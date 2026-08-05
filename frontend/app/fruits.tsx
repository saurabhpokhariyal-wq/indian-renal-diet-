import { FoodGuideLayout } from "@/src/components/FoodGuideLayout";
import { api } from "@/src/lib/api";
import { useLang } from "@/src/lib/language-context";

export default function FruitsGuideScreen() {
  const { t } = useLang();
  return (
    <FoodGuideLayout
      fetchGuide={api.getFruitGuide as any}
      title={t("fruitGuideTitle")}
      subtitle={t("fruitGuideSubtitle")}
      intro={t("fruitGuideIntro")}
      introIcon="information-circle"
      introTheme="brand"
      entriesKey="fruits"
      testIdPrefix="fruit"
      backTestIdPrefix="fruits"
      errorLabel="Failed to load fruits guide"
    />
  );
}
