import { Page, Text, Spinner } from '@shopify/polaris';

export default function AuthInstallPage() {
  return (
    <Page>
      <Text variant="headingLg" as="h1">
        App Installation in Progress
      </Text>
      <Spinner accessibilityLabel="Loading" size="large" />
      <Text as="p">
        Please wait while we complete your Shopify app installation. You will be redirected automatically when the process is complete.
      </Text>
    </Page>
  );
}
