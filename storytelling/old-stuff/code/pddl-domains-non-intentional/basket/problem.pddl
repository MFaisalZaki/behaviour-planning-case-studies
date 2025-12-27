(define (problem problem-basketball)(:domain domain-basketball)
 
(:requirements :adl :typing :negative-preconditions)

(:objects


; vase - item

; handcuff - item
; theft - crime
; murder - crime
	
; problem object
alice-home - place
bob-home - place
david-home - place
charlie-home - place
basketcourt - place
downtown - place
policestation - place

alice - citizen
bob - citizen
charlie - citizen
david - citizen
sherlock - detective
lestrade - inspector

gun bat basketball - item


)

(:init

	; (at ?object - object ?place - place)
	; (alive ?character - character)
	; (murder ?murderer - character ?victim - character)
	; (has ?character - character ?item - item)

  (alive alice)
  (alive bob) 
  (alive charlie) 
  (alive david) 
  (alive sherlock)
  (alive lestrade)

  (at alice alice-home)
  (at bob bob-home)
  (at charlie charlie-home)
  (at david david-home)
  
  (at sherlock policestation)
  (at lestrade policestation)
  
  (at bat charlie-home)
  (at gun bob-home)
  (at basketball david-home)

  (owns charlie bat)
  (weapon bat)
  (owns-place charlie charlie-home)

  (owns bob gun)
  (weapon gun)
  (owns-place bob bob-home)
  
  (owns david basketball)
  (weapon basketball)
  (owns-place david david-home)
  
  ; (intends bob (dead alice))
  ; (intends charlie (dead alice))
  ; (intends david (dead alice))

  ; (intends bob (get-away bob))
  ; (intends charlie (get-away charlie))
  ; (intends david (get-away david))
)

(:goal (and
  (exists (?c - character) (dead ?c))
  (exists (?c - character) (arressted ?c)))
  
)

)
