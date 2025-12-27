;;;
;;; A domain for telling a story about an evil bank robber in the Wild West
;;; Originally created by James Niehaus for his dissertation
;;; Adapted and corrected by Stephen G. Ware
;;;
(define (domain heist)
  (:requirements :adl)
  (:types 
          character thing place poker-game - object
          mobile bystanders seller pawn-broker - character
          evil sheriff guard - mobile
          bank bar store alley - place
          big-money mother-lode - money
          gun cuffs small-goods valuable money - thing
		      horse - valuable
  )
  
  (:predicates (connected ?from - place ?to - place)
               (alley-of ?alley - alley ?place - place)
               (at ?object - object ?place - place)
               ;(at ?character - character ?place - place)
               ;(at ?poker-game - poker-game ?place - place)
               (has ?object - object ?thing - thing)
              ;  (has ?bank - bank ?money - money)
               (open ?store - store)
               (forsale ?thing - thing ?store - store)
               (hidden ?character - character)
               (drunk ?character - character)
               (sleeping ?character - character)
               (in-cuffs ?character - character ?cuffs - cuffs)
               (free-with-money ?character - character)
               (friendly ?friend - character ?character - character)
               (blocking ?character - character ?alley - alley)
               (guard-of ?character - character ?place - place)
               (guarded ?place - place)
               (bet-at ?money - money ?poker-game - poker-game)
               (held-up ?character - character ?bank - bank)
               (arrested ?sheriff - sheriff ?character - character)
               (the-end)
               )

  ;; Pick something up.
  (:action pick-up
    :parameters   (?character - character ?thing - thing ?place - place)
    :precondition (and (at ?character ?place)
                       (at ?thing ?place))
    :effect       (and (not (at ?thing ?place))
                       (has ?character ?thing))
    )

  ;; Pick up and holster a gun.
  (:action holster-gun
    :parameters   (?character - character ?gun - gun ?place - place)
    :precondition (and (at ?character ?place)
                       (at ?gun ?place))
    :effect       (and (not (at ?gun ?place))
                       (has ?character ?gun))
    )

  ;; Withdraw some money from the bank.
  (:action withdraw-money
    :parameters   (?character - character ?bank - bank ?money - money)
    :precondition (and (at ?character ?bank)
                       (has ?bank ?money))
    :effect       (and (not (has ?bank ?money))
                       (has ?character ?money))
    )

  ;; Open a store for business.
  (:action open_action
    :parameters   (?character - character ?store - store)
    :precondition (at ?character ?store)
    :effect       (open ?store))

  ;; Sell some small goods.
  (:action sell
    :parameters   (?character - character ?buyer - character ?thing - small-goods ?money - money ?place - place)
    :precondition (and (at ?character ?place)
                       (has ?character ?thing)
                       (at ?buyer ?place)
                       (has ?buyer ?money))
    :effect       (and (not (has ?character ?thing))
                       (has ?character ?money)
                       (not (has ?buyer ?money))
                       (has ?buyer ?thing))
    )

  ;; Buy a dress (or other good) from a store.
  (:action buy-dress
    :parameters   (?character - character ?thing - valuable ?store - store ?money - money)
    :precondition (and (open ?store)
                       (forsale ?thing ?store)
                       (at ?character ?store)
                       (has ?character ?money))
    :effect       (and (has ?character ?thing)
                       (not (forsale ?thing ?store))
                       (not (has ?character ?money)))
    )

  ;; Fail to buy a dress (or other good) from a store because of no money.
  (:action fail-buy-dress
    :parameters   (?character - character ?thing - valuable ?store - store ?money - money)
    :precondition (and (open ?store)
                       (forsale ?thing ?store)
                       (at ?character ?store)
                       (not (has ?character ?money)))
    )

  ;; kick someone out of the way.
  (:action kick-out-of-way
    :parameters   (?character - evil ?roadblock - character ?alley - alley ?place - place)
    :precondition (and (at ?character ?place)
                       (at ?roadblock ?place)
                       (blocking ?roadblock ?alley))
    :effect       (not (blocking ?roadblock ?alley))
    )

  ;; Hatch a plan to rob the bank.
  (:action hatch-plan
    :parameters   (?character - evil ?gun - gun ?horse - horse ?bank - bank ?mother-lode - mother-lode)
    :precondition (has ?bank ?mother-lode)
    :effect       (and (not (has ?character ?mother-lode))
                       (has ?character ?gun)
                       (has ?character ?horse)
                       (has ?character ?mother-lode)
                       (free-with-money ?character)))

  ;; Hide in an alley.
  (:action hide-in-dark-alley
    :parameters   (?character - evil ?alley - alley)
    :precondition (at ?character ?alley)
    :effect       (hidden ?character)
    )

  ;; Pickpocket.
  (:action pickpocket
    :parameters   (?character - evil ?mark - character ?money - money ?place - place ?alley - alley)
    :precondition (and (alley-of ?alley ?place)
                       (at ?character ?alley)
                       (at ?mark ?place)
                       (hidden ?character)
                       (has ?mark ?money))
    :effect       (and (has ?character ?money)
                       (not (has ?mark ?money))
                       (not (hidden ?character)))
    )

  ;; Move.
  (:action move-once
    :parameters   (?character - mobile ?from - place ?to - place)
    :precondition (and (connected ?from ?to)
                       (at ?character ?from))
    :effect       (and (at ?character ?to)
                       (not (at ?character ?from)))
    )

  ;; Buy drinks for (and get drunk).
  (:action buy-drinks-for
    :parameters   (?character - character ?drinker - character ?money - money ?place - bar)
    :precondition (and (at ?character ?place)
                       (at ?drinker ?place)
                       (has ?character ?money))
    :effect       (and (friendly ?drinker ?character)
                       (drunk ?drinker))
    )

  ;; Cheat at a poker game (put up some money).
  (:action cheat-at-poker
    :parameters   (?character - evil ?poker - poker-game ?money - money ?winnings - money ?place - place)
    :precondition (and (at ?character ?place)
                       (at ?poker ?place)
                       (has ?character ?money)
                       (bet-at ?winnings ?poker))
    :effect       (has ?character ?winnings)
    )

  ;; Leave with.
  (:action escort-drunk-friend
    :parameters   (?character - character ?friend - character ?from - place ?to - place)
    :precondition (and (connected ?from ?to)
                       (at ?character ?from)
                       (at ?friend ?from)
                       (drunk ?friend)
                       (friendly ?friend ?character))
    :effect       (and (not (at ?character ?from))
                       (at ?character ?to)
                       (not (at ?friend ?from))
                       (at ?friend ?to))
    )

  ;; Lay to rest in alley.
  (:action lay-to-rest-in-alley
    :parameters   (?character - character ?friend - guard ?place - alley ?bank - bank)
    :precondition (and (at ?character ?place)
                       (at ?friend ?place)
                       (drunk ?friend)
                       (friendly ?friend ?character)
                       (guard-of ?friend ?bank))
    :effect       (and (sleeping ?friend)
                       (not (guarded ?bank)))
    )

  ;; Take item off sleeping character,
  (:action take-thing-off-sleeper
    :parameters   (?character - character ?sleeper - character ?thing - thing ?place - alley)
    :precondition (and (at ?character ?place)
                       (at ?sleeper ?place)
                       (sleeping ?sleeper)
                       (has ?sleeper ?thing))
    :effect       (and (has ?character ?thing)
                       (not (has ?sleeper ?thing)))
    )

  ;; Pawn a valuable for money.
  (:action pawn-valuable
    :parameters   (?character - character ?pawn-broker - pawn-broker ?thing - valuable ?place - place ?big-money - big-money)
    :precondition (and (at ?character ?place)
                       (at ?pawn-broker ?place)
                       (has ?character ?thing)
                       (has ?pawn-broker ?big-money))
    :effect       (and (not (has ?character ?thing))
                       (has ?pawn-broker ?thing)
                       (has ?character ?big-money))
    )

  ;; Buy a horse.
  (:action buy-valuable
    :parameters   (?character - character ?seller - seller ?thing - valuable ?place - place ?big-money - big-money)
    :precondition (and (has ?seller ?thing)
                       (at ?character ?place)
                       (at ?seller ?place)
                       (has ?character ?big-money))
    :effect       (and (has ?character ?thing)
                       (not (has ?seller ?thing))
                       (not (has ?character ?big-money)))
    )

  ;; Ride a horse to a location.
  (:action ride-horse-to
    :parameters   (?character - mobile ?horse - horse ?from - place ?to - place)
    :precondition (and (connected ?from ?to)
                       (at ?character ?from)
                       (at ?horse ?from)
                       (has ?character ?horse))
    :effect       (and (at ?character ?to)
                       (not (at ?character ?from))
                       (at ?horse ?to)
                       (not (at ?horse ?from)))
    )

  ;; Hold up a bank.
  (:action hold-up-bank
    :parameters   (?character - evil ?gun - gun ?bank - bank ?sheriff - sheriff)
    :precondition (and (at ?character ?bank)
                       (has ?character ?gun)
                       (not (guarded ?bank)))
    :effect       (and (held-up ?character ?bank)
                       (arrested ?sheriff ?character))
    )

  ;; Collect money.
  (:action collect-money-from-heist
    :parameters   (?character - evil ?bank - bank ?mother-lode - mother-lode)
    :precondition (and (at ?character ?bank)
                       (held-up ?character ?bank)
                       (has ?bank ?mother-lode))
    :effect       (and (has ?character ?mother-lode)
                       (not (held-up ?character ?bank))
                       (not (has ?bank ?mother-lode)))
    )

  ;; Getaway with stolen money.
  (:action getaway-with-money
    :parameters   (?character - evil ?mother-lode - mother-lode ?horse - horse ?place - place ?dest - place)
    :precondition (and (connected ?place ?dest)
                       (at ?character ?place)
                       (at ?horse ?place)
                       (has ?character ?mother-lode))
    :effect       (and (not (at ?character ?place))
                       (not (at ?horse ?place))
                       (free-with-money ?character)
                       (at ?character ?dest))
    )

;  ;; Bystanders sound alarm.
;  (:action alert-sheriff
;    :parameters   (?character - evil ?bystanders - bystanders ?sheriff - sheriff ?bank - bank)
;    :precondition (and (at ?character ?bank)
;                       (held-up ?character ?bank))
;    :effect       (knows ?sheriff (held-up ?character ?bank)))

  ;; Arrest.
  (:action arrest
    :parameters   (?criminal - evil ?sheriff - sheriff ?place - place ?cuffs - cuffs ?money - money)
    :precondition (and (at ?sheriff ?place)
                       (at ?criminal ?place)
                       (has ?sheriff ?cuffs)
                       (has ?criminal ?money))
    :effect       (and (arrested ?sheriff ?criminal)
                       (in-cuffs ?criminal ?cuffs)
                       (has ?sheriff ?money)
                       (not (has ?criminal ?money)))
    )
  
  )