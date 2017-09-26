type ('nonterminal, 'terminal) symbol =
  | N of 'nonterminal
  | T of 'terminal

(* this builds the function that will be curried into the production function *)
let rec build_grammar_fun rules symbol =

    (* iterate through rules returning list of rules pertaining to the symbol *)
    match rules with
    (a,b)::l when a = symbol -> b::(build_grammar_fun l symbol)
    | (a,b)::l -> (build_grammar_fun l symbol)
    | _ -> []

let rec convert_grammar gram1 = 
   
    (* extract rules and start symbol*) 
    let rules = (fun (x,y) -> y) gram1 in 
    let start = (fun (x,y) -> x) gram1 in

    (* recurse through rules and build production function *)
    let production_function = build_grammar_fun rules in
    
    (* return grammar now in hw2 style *)
    (start, production_function)

(* main prob *)
   
(* go through the rules one at a time*)
let rec match_rules_list gram start rules derivation accept frag = 

    match rules with

    (* if there are no rules to match then we're done *)
    [] -> None
   
    (* try to match fragment with first rule *)
    |first_rule::remaining_rules -> match (match_rule gram start (first_rule) (derivation@[(start, first_rule)]) accept frag) with 

                                    (* if there is no match try next rule *)
                                    | None -> (match_rules_list gram start remaining_rules derivation accept frag)

                                    (* if there is a match extract the returned data *)
                                    | Some (derivation_updated, suffix) -> Some(derivation_updated, suffix)

(* match single rule with fragment *)
and match_rule gram start rule derivation accept frag = 

    (* iterate through each element of the rule *)
    match rule with

    (* if rule list is empty we've matched everything so accept *)
    [] -> accept derivation frag

    (* if the first element in rule is terminal see if it matches the frag *)
    | T(x)::remaining_rule_elements -> (match frag with 
                                       [] -> None
                                       | h::t -> if h = x then (match_rule gram start remaining_rule_elements derivation accept t) else (None))

    (* non-terminal terms are basically new rule lists so call match_rules_list again *)
    | N(x)::remaining_rule_elements -> (match_rules_list gram x (gram x) derivation (fun derivation1 frag1 -> match_rule gram x remaining_rule_elements derivation1 accept frag1) frag)

(* returns a funciton that takes an acceptor and a fragment *)
let parse_prefix gram =
    let start = fst(gram) in
    let gram_fun = snd(gram) in
    (match_rules_list gram_fun start (gram_fun start) [])




