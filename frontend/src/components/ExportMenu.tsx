import {
  Button,
  Menu,
  MenuDivider,
  MenuGroup,
  MenuGroupHeader,
  MenuItem,
  MenuList,
  MenuPopover,
  MenuTrigger,
  Spinner,
  Tooltip,
} from '@fluentui/react-components';
import {
  ArrowDownload20Regular,
  BookOpen20Regular,
  Braces20Regular,
  CheckmarkCircle16Filled,
  ChevronDown16Regular,
  DocumentPdf20Regular,
  DocumentText20Regular,
  SlideText20Regular,
  Warning16Filled,
} from '@fluentui/react-icons';
import { useQuery } from '@tanstack/react-query';
import { useState, type ReactElement } from 'react';
import api from '../lib/api';
import { downloadFile } from '../lib/download';
import { useToast } from './ToastProvider';

interface ExportStatus {
  status: 'draft' | 'final';
  unconfirmed: string[];
  unconfirmed_count: number;
}

interface ExportOption {
  key: string;
  label: string;
  hint: string;
  path: string;
  ext: string;
  icon: ReactElement;
}

interface ExportMenuProps {
  initiativeId: string;
  hasCompendium?: boolean;
  /** Shown as a link in the draft chip, e.g. scroll to the confirm section. */
  onReviewDraft?: () => void;
  appearance?: 'primary' | 'secondary';
}

export function exportStatusKey(id: string) {
  return ['export-status', id] as const;
}

export function ExportMenu({ initiativeId, hasCompendium, onReviewDraft, appearance = 'primary' }: ExportMenuProps) {
  const { showToast } = useToast();
  const [busy, setBusy] = useState<string | null>(null);
  const status = useQuery({
    queryKey: exportStatusKey(initiativeId),
    queryFn: async () => (await api.get<ExportStatus>(`/initiatives/${initiativeId}/export-status`)).data,
  });

  const base = `/initiatives/${initiativeId}`;
  const briefOptions: ExportOption[] = [
    { key: 'pdf', label: 'PDF brief', hint: 'Print-ready one-pager', path: `${base}/export.pdf`, ext: 'pdf', icon: <DocumentPdf20Regular /> },
    { key: 'pptx', label: 'PowerPoint deck', hint: '16:9 slides for steering', path: `${base}/export.pptx`, ext: 'pptx', icon: <SlideText20Regular /> },
    { key: 'md', label: 'Markdown', hint: 'Paste into Confluence or Teams', path: `${base}/export.md`, ext: 'md', icon: <DocumentText20Regular /> },
    { key: 'json', label: 'JSON', hint: 'Full record, re-importable', path: `${base}/export.json`, ext: 'json', icon: <Braces20Regular /> },
  ];
  const compendiumOption: ExportOption = {
    key: 'compendium',
    label: 'Evidence compendium',
    hint: 'Literature review as Markdown',
    path: `${base}/compendium.md`,
    ext: 'md',
    icon: <BookOpen20Regular />,
  };

  const run = async (opt: ExportOption) => {
    setBusy(opt.key);
    try {
      const name = await downloadFile(opt.path, `impact-brief.${opt.ext}`);
      const draft = status.data?.status === 'draft';
      showToast({
        title: `${opt.label} downloaded`,
        body: draft ? `${name} — marked DRAFT until all values are confirmed.` : name,
        intent: 'success',
      });
    } catch (e) {
      showToast({ title: `${opt.label} export failed`, body: e instanceof Error ? e.message : String(e), intent: 'error' });
    } finally {
      setBusy(null);
    }
  };

  const draft = status.data?.status === 'draft';
  // Scorecard ranges mirror the estimates and are confirmed with them, so count estimates when present.
  const pending = status.data?.unconfirmed ?? [];
  const estimatePending = pending.filter((p) => p.startsWith('estimates')).length;
  const count = estimatePending || pending.length;
  const noun = estimatePending ? (count === 1 ? 'estimate' : 'estimates') : count === 1 ? 'value' : 'values';

  const item = (opt: ExportOption) => (
    <MenuItem
      key={opt.key}
      icon={busy === opt.key ? <Spinner size="extra-tiny" /> : opt.icon}
      disabled={!!busy}
      onClick={() => void run(opt)}
    >
      <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.3, padding: '2px 0' }}>
        <span style={{ fontWeight: 600 }}>{opt.label}</span>
        <span style={{ fontSize: 12, color: 'var(--text-3)' }}>{opt.hint}</span>
      </div>
    </MenuItem>
  );

  return (
    <div className="row gap-8">
      {status.data &&
        (draft ? (
          <Tooltip
            relationship="description"
            content="Every export is labelled DRAFT until the LLM-suggested estimates are confirmed or edited."
          >
            <span className="pill pill-warning">
              <Warning16Filled />
              Draft · {count} {noun} to confirm
              {onReviewDraft && (
                <button
                  type="button"
                  onClick={onReviewDraft}
                  style={{
                    border: 'none',
                    background: 'none',
                    padding: 0,
                    font: 'inherit',
                    color: 'inherit',
                    textDecoration: 'underline',
                    cursor: 'pointer',
                  }}
                >
                  Review
                </button>
              )}
            </span>
          </Tooltip>
        ) : (
          <span className="pill pill-success">
            <CheckmarkCircle16Filled /> Final
          </span>
        ))}
      <Menu positioning="below-end">
        <MenuTrigger disableButtonEnhancement>
          <Button
            appearance={appearance}
            className={appearance === 'primary' ? 'btn-primary' : undefined}
            icon={busy ? <Spinner size="tiny" /> : <ArrowDownload20Regular />}
            iconPosition="before"
          >
            Export <ChevronDown16Regular style={{ marginLeft: 4 }} />
          </Button>
        </MenuTrigger>
        <MenuPopover style={{ minWidth: 260 }}>
          <MenuList>
            <MenuGroup>
              <MenuGroupHeader>Impact brief</MenuGroupHeader>
              {briefOptions.map(item)}
            </MenuGroup>
            {hasCompendium && (
              <>
                <MenuDivider />
                <MenuGroup>
                  <MenuGroupHeader>Evidence</MenuGroupHeader>
                  {item(compendiumOption)}
                </MenuGroup>
              </>
            )}
          </MenuList>
        </MenuPopover>
      </Menu>
    </div>
  );
}
