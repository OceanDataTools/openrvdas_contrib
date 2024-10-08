import { test, expect } from '@grafana/plugin-e2e';

test('table query should show streaming data', async ({ panelEditPage, selectors, readProvisionedDataSource }) => {
  const ds = await readProvisionedDataSource({ fileName: 'datasources.yml' });
  await panelEditPage.datasource.set(ds.name);
  await panelEditPage.setVisualization('Table');
  await panelEditPage.getQueryEditorRow('A').getByTestId('fields').fill('test');
  await panelEditPage.getQueryEditorRow('A').getByTestId('seconds').fill('1');
  const refreshPanelButton = panelEditPage.getByGrafanaSelector(selectors.components.RefreshPicker.runButtonV2, {
    root: panelEditPage.getByGrafanaSelector(selectors.components.PanelEditor.General.content),
  });
  await refreshPanelButton.click();
  await expect(panelEditPage.panel.fieldNames).toContainText(['time', 'value']);
});
