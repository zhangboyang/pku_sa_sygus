

(set-logic LIA)

(synth-fun f ((x Int)) Int
    ((Start Int (
                 x
                 3
                 7
                 10
                 (* Start Start)
                 (mod Start Start)))))

(declare-var x Int)

(constraint (= (f x) x))

(check-synth)

