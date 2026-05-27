import type { MicPromptText, SceneFrameData } from './types';
import { ProductionPrompt } from './ProductionPrompt';
import { SceneFrame } from './SceneFrame';

type MiniRoleplayProps = {
  scenario?: string;
  frame?: SceneFrameData;
  productionCue?: string;
  targetMeaning?: string;
  micText?: MicPromptText;
};

export function MiniRoleplay({
  scenario = 'Mini roleplay scenario',
  frame,
  productionCue,
  targetMeaning,
  micText,
}: MiniRoleplayProps) {
  return (
    <section className="mini-roleplay">
      <h2>{scenario}</h2>
      <SceneFrame frame={frame} />
      <ProductionPrompt cue={productionCue} targetMeaning={targetMeaning} micText={micText} />
    </section>
  );
}
