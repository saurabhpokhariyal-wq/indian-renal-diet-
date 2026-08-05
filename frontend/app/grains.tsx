import { FoodGuideLayout } from "@/src/components/FoodGuideLayout";
import { api } from "@/src/lib/api";
import { useLang } from "@/src/lib/language-context";

export default function GrainsGuideScreen() {
  const { t } = useLang();
  return (
    <FoodGuideLayout
      fetchGuide={api.getGrainGuide as any}
      title={t("grainGuideTitle")}
      subtitle={t("grainGuideSubtitle")}
      intro={t("grainGuideIntro")}
      introIcon="pizza"
      introTheme="brand"
      entriesKey="grains"
      testIdPrefix="grain"
      backTestIdPrefix="grains"
      errorLabel="Failed to load grains guide"
    />
  );
}
