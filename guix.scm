;; Social-Media-Dipstick - Guix Package Definition
;; Run: guix shell -D -f guix.scm

(use-modules (guix packages)
             (guix gexp)
             (guix git-download)
             (guix build-system gnu)
             ((guix licenses) #:prefix license:)
             (gnu packages base))

(define-public social_media_dipstick
  (package
    (name "Social-Media-Dipstick")
    (version "0.1.0")
    (source (local-file "." "Social-Media-Dipstick-checkout"
                        #:recursive? #t
                        #:select? (git-predicate ".")))
    (build-system gnu-build-system)
    (synopsis "Guix channel/infrastructure")
    (description "Guix channel/infrastructure - part of the RSR ecosystem.")
    (home-page "https://github.com/hyperpolymath/Social-Media-Dipstick")
    (license license:agpl3+)))

;; Return package for guix shell
social_media_dipstick
