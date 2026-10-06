import { ContactSection } from "@/components/landing/ContactSection";
import { CtaSection } from "@/components/landing/CtaSection";
import { DashboardPreviewSection } from "@/components/landing/DashboardPreviewSection";
import { ExtensionShowcaseSection } from "@/components/landing/ExtensionShowcaseSection";
import { FaqSection } from "@/components/landing/FaqSection";
import { FeaturesSection } from "@/components/landing/FeaturesSection";
import { HeroSection } from "@/components/landing/HeroSection";
import { HowItWorksSection } from "@/components/landing/HowItWorksSection";
import { OverviewSection } from "@/components/landing/OverviewSection";
import { ScannerShowcaseSection } from "@/components/landing/ScannerShowcaseSection";
import { StatsSection } from "@/components/landing/StatsSection";
import { TestimonialsSection } from "@/components/landing/TestimonialsSection";
import { ThreatIntelSection } from "@/components/landing/ThreatIntelSection";
import { useAuth } from "@/context/AuthContext";

export function HomePage() {
  const { isAuthenticated } = useAuth();

  return (
    <div>
      <HeroSection isAuthenticated={isAuthenticated} />
      <StatsSection />
      <OverviewSection />
      <FeaturesSection />
      <HowItWorksSection />
      <ScannerShowcaseSection />
      <ExtensionShowcaseSection />
      <ThreatIntelSection />
      <DashboardPreviewSection />
      <TestimonialsSection />
      <FaqSection />
      <ContactSection />
      <CtaSection isAuthenticated={isAuthenticated} />
    </div>
  );
}
