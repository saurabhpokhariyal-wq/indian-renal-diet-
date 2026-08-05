import { FoodGuideLayout } from "@/src/components/FoodGuideLayout";
import { api } from "@/src/lib/api";
import { useLang } from "@/src/lib/language-context";

export default function SnacksGuideScreen() {
  const { t } = useLang();
  return (
    <FoodGuideLayout
      fetchGuide={api.getSnackGuide as any}
      title={t("snackGuideTitle")}
      subtitle={t("snackGuideSubtitle")}
      intro={t("snackGuideIntro")}
      introIcon="cafe"
      introTheme="brand"
      entriesKey="snacks"
      testIdPrefix="snack"
      backTestIdPrefix="snacks"
      errorLabel="Failed to load snacks guide"
    />
  );
}
