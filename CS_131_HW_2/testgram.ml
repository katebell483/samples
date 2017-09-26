type work_nonterminals = | Interview | Hired | Fired | Quit | Promoted | Emotion | Gday | Bday 

let work_grammar = 
   (Interview, 
    function
        | Interview -> 
            [[N Hired; N Emotion; N Gday]; 
            [N Emotion; N Interview]];
        | Hired ->
            [[N Quit];
            [N Emotion; N Gday];
            [N Bday];
            [N Emotion]]
        | Fired -> 
            [[N Bday; N Gday];
            [N Emotion];
            [N Hired]]
        | Quit -> 
            [[N Emotion];
            [N Gday; T"realize no money"; N Bday];
            [T"anxiety"; N Emotion; T"anxiety"];
            [N Hired]]
        | Promoted ->
            [[N Hired; N Gday];
            [N Gday];
            [N Emotion]]
        | Emotion -> 
            [[T"happy"];
            [T"sad"];
            [T"confused"];
            [T"anxious"];
            [T"nervous"];
            [T"relieved"]]
        | Gday -> 
            [[T"you had a good day"]]
        | Bday -> 
            [[T"you had a bad day"]])


let ends_in_good_day rules =
    match (List.tl rules) with
    | (Gday,_)::_ -> true
    | _ -> false

let accept_only_good_days_in_the_end rules frag =
    if ends_in_good_day rules then Some(rules, frag) else None

let test5 =
  ((parse_prefix work_grammar accept_only_good_days_in_the_end ["happy"; "anxious"; "you had a good
day"] 

= Some(
    [(Interview, [N Hired; N Emotion; N Gday]); (Hired, [N Quit]); (Quit, [N
    Gday; T "realize no money"; N Bday]); (Gday, [T "you had a good day"]); (Bday,
    [T "you had a bad day"]); (Emotion, [T "anxious"]); (Interview, [N Emotion; N
    Interview]); ( Emotion, [T "anxious"]); (Interview, [N Hired; N Emotion; N
    Gday]); (Hired, [N Emotion]); (Emotion, [T "relieved"]); (Gday, [T"you had a good
    day"])], [])))








