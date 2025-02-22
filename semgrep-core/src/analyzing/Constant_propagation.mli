val hook_constant_propagation_and_evaluate_literal :
  (AST_generic.expr -> AST_generic.svalue option) option ref
(** Provide the analysis with extra information about constants. *)

val constant_propagation_and_evaluate_literal :
  ?lang:Lang.t -> AST_generic.expr -> AST_generic.svalue option
(** Partially evaluate a Generic expression. *)

(* Works by side effect on the generic AST by modifying its refs.
 * We pass the lang because some constant propagation algorithm may be
 * specific to a language.
 *)
(* !Note that this assumes Naming_AST.resolve has been called before! *)
val propagate_basic : Lang.t -> AST_generic.program -> unit

val propagate_dataflow : Lang.t -> AST_generic.program -> unit
