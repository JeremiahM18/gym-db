import type { ActionLink } from "../features/gym-browser/types";

export function ActionPill(props: ActionLink) {
  return (
    <a className={`action-pill ${props.tone ?? "ink"}`} href={props.href} target="_blank" rel="noreferrer">
      {props.label}
    </a>
  );
}
