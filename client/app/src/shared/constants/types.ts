export type DisplayStepErrorsFunction = (index: number) => boolean | undefined;
export type StepFormFunction = (index: number) => any;
export type cancelFun = null;
export type ConfirmFunFunction = (receiver_id: { id: number }) => void;