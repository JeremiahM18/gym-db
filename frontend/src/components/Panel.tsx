import type { ReactNode } from "react";

type PanelProps = {
  title: string;
  subtitle?: string;
  children: ReactNode;
  accent?: string;
};

export function Panel(props: PanelProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">{props.accent ?? "GymDB"}</p>
          <h2>{props.title}</h2>
        </div>
        {props.subtitle ? <p className="panel-subtitle">{props.subtitle}</p> : null}
      </div>
      {props.children}
    </section>
  );
}
