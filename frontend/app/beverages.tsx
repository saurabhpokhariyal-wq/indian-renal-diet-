import { FoodGuideLayout } from "@/src/components/FoodGuideLayout";
import { api } from "@/src/lib/api";
import { useLang } from "@/src/lib/language-context";

export default function BeveragesGuideScreen() {
  const { t } = useLang();
  return (
    <FoodGuideLayout
      fetchGuide={api.getBeverageGuide as any}
      title={t("beverageGuideTitle")}
      subtitle={t("beverageGuideSubtitle")}
      intro={t("beverageGuideIntro")}
      introIcon="water"
      introTheme="aiBlue"
      entriesKey="beverages"
      testIdPrefix="beverage"
      backTestIdPrefix="beverages"
      showFluidChip
      errorLabel="Failed to load beverage guide"
    />
  );
}
