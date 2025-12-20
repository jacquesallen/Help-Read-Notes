\version "2.24.3"

\header {
  title = "Piano Note Reading Guide for Parents"
  subtitle = "Middle C, D (Treble Clef) and B (Bass Clef)"
  tagline = ##f
}

\paper {
  #(set-paper-size "a4")
  top-margin = 15\mm
  bottom-margin = 15\mm
  left-margin = 20\mm
  right-margin = 20\mm
}

% ============================================
% INTRODUCTION
% ============================================

\markup {
  \column {
    \vspace #1
    \bold \larger "Introduction"
    \vspace #0.5
    \justify {
      This guide will help you understand three important notes that beginners learn on the piano:
      Middle C and D in the treble clef (right hand), and B in the bass clef (left hand).
      We will also look at four different note lengths (rhythmic values) so you can help your
      child recognise how long to hold each note.
    }
    \vspace #1
  }
}

% ============================================
% UNDERSTANDING THE STAFF
% ============================================

\markup {
  \column {
    \bold \larger "Understanding the Staff"
    \vspace #0.5
    \justify {
      Music is written on a staff made up of five horizontal lines. The treble clef
      (used for higher notes, typically played with the right hand) and the bass clef
      (used for lower notes, typically played with the left hand) tell us which notes
      the lines and spaces represent.
    }
    \vspace #0.5
  }
}

% ============================================
% MIDDLE C
% ============================================

\markup {
  \column {
    \vspace #1
    \bold \larger "1. Middle C (Treble Clef)"
    \vspace #0.5
    \justify {
      Middle C is one of the most important notes on the piano. It sits on a short line
      called a "ledger line" just below the treble clef staff. On the piano keyboard,
      Middle C is located roughly in the center of the keyboard.
    }
    \vspace #0.5
    \italic "How to recognise Middle C:"
    \line { "- It sits on its own ledger line below the five main lines" }
    \line { "- The ledger line goes through the middle of the note head" }
    \vspace #0.5
  }
}

\markup { \bold "Middle C in four different note lengths:" }

\score {
  \new Staff \with {
    instrumentName = "Treble"
  } {
    \clef treble
    \time 4/4
    % Crotchet (quarter note)
    c'4^\markup { \small "Crotchet" } r4 r2 \bar "||"
    % Minim (half note)
    c'2^\markup { \small "Minim" } r2 \bar "||"
    % Dotted minim (dotted half note)
    c'2.^\markup { \small "Dotted Minim" } r4 \bar "||"
    % Semibreve (whole note)
    c'1^\markup { \small "Semibreve" } \bar "|."
  }
  \layout {
    indent = 15\mm
  }
}

% ============================================
% D IN TREBLE CLEF
% ============================================

\markup {
  \column {
    \vspace #1.5
    \bold \larger "2. D (Treble Clef)"
    \vspace #0.5
    \justify {
      D is the note just above Middle C. It sits in the space just below the first
      (bottom) line of the treble clef staff. On the piano, D is the white key
      immediately to the right of Middle C.
    }
    \vspace #0.5
    \italic "How to recognise D:"
    \line { "- It hangs just below the bottom line of the treble staff" }
    \line { "- It is in the space between Middle C's ledger line and the staff" }
    \vspace #0.5
  }
}

\markup { \bold "D in four different note lengths:" }

\score {
  \new Staff \with {
    instrumentName = "Treble"
  } {
    \clef treble
    \time 4/4
    % Crotchet (quarter note)
    d'4^\markup { \small "Crotchet" } r4 r2 \bar "||"
    % Minim (half note)
    d'2^\markup { \small "Minim" } r2 \bar "||"
    % Dotted minim (dotted half note)
    d'2.^\markup { \small "Dotted Minim" } r4 \bar "||"
    % Semibreve (whole note)
    d'1^\markup { \small "Semibreve" } \bar "|."
  }
  \layout {
    indent = 15\mm
  }
}

% ============================================
% B IN BASS CLEF
% ============================================

\markup {
  \column {
    \vspace #1.5
    \bold \larger "3. B (Bass Clef)"
    \vspace #0.5
    \justify {
      B in the bass clef sits on the middle line of the bass staff. This is the B
      just below Middle C on the piano keyboard. It is played with the left hand.
    }
    \vspace #0.5
    \italic "How to recognise B:"
    \line { "- It sits directly on the middle (third) line of the bass staff" }
    \line { "- The line goes through the centre of the note head" }
    \vspace #0.5
  }
}

\markup { \bold "B in four different note lengths:" }

\score {
  \new Staff \with {
    instrumentName = "Bass"
  } {
    \clef bass
    \time 4/4
    % Crotchet (quarter note)
    b4^\markup { \small "Crotchet" } r4 r2 \bar "||"
    % Minim (half note)
    b2^\markup { \small "Minim" } r2 \bar "||"
    % Dotted minim (dotted half note)
    b2.^\markup { \small "Dotted Minim" } r4 \bar "||"
    % Semibreve (whole note)
    b1^\markup { \small "Semibreve" } \bar "|."
  }
  \layout {
    indent = 15\mm
  }
}

% ============================================
% UNDERSTANDING RHYTHMIC VALUES
% ============================================

\markup {
  \column {
    \vspace #1.5
    \bold \larger "Understanding Note Lengths (Rhythmic Values)"
    \vspace #0.5
    \justify {
      Notes come in different shapes to show how long they should be held.
      Here are the four main note values your child will learn:
    }
    \vspace #0.5
  }
}

\markup {
  \column {
    \vspace #0.3
    \bold "Crotchet (Quarter Note) - 1 beat"
    \justify {
      A filled-in (black) note head with a stem. Count: "1"
    }
  }
}

\score {
  \new Staff {
    \clef treble
    \time 4/4
    c'4 d'4 c'4 d'4 \bar "|."
  }
  \layout { }
}

\markup {
  \column {
    \vspace #0.5
    \bold "Minim (Half Note) - 2 beats"
    \justify {
      An open (white/hollow) note head with a stem. Count: "1 - 2"
    }
  }
}

\score {
  \new Staff {
    \clef treble
    \time 4/4
    c'2 d'2 \bar "|."
  }
  \layout { }
}

\markup {
  \column {
    \vspace #0.5
    \bold "Dotted Minim (Dotted Half Note) - 3 beats"
    \justify {
      An open note head with a stem and a dot beside it. The dot adds half
      the value of the note (2 + 1 = 3 beats). Count: "1 - 2 - 3"
    }
  }
}

\score {
  \new Staff {
    \clef treble
    \time 3/4
    c'2. \bar "||"
    d'2. \bar "|."
  }
  \layout { }
}

\markup {
  \column {
    \vspace #0.5
    \bold "Semibreve (Whole Note) - 4 beats"
    \justify {
      An open note head with NO stem. This is the longest common note.
      Count: "1 - 2 - 3 - 4"
    }
  }
}

\score {
  \new Staff {
    \clef treble
    \time 4/4
    c'1 \bar "||"
    d'1 \bar "|."
  }
  \layout { }
}

% ============================================
% COMPARISON CHART
% ============================================

\markup {
  \column {
    \vspace #1.5
    \bold \larger "Quick Reference: All Three Notes with All Four Rhythms"
    \vspace #0.5
    \justify {
      Below is a complete reference showing Middle C, D, and B with each rhythmic value.
    }
    \vspace #0.5
  }
}

\score {
  <<
    \new Staff \with {
      instrumentName = "Treble"
    } {
      \clef treble
      \time 4/4
      \mark \markup { \bold "Middle C" }
      c'4 c'4 c'4 c'4 \bar "||"
      c'2 c'2 \bar "||"
      \time 3/4
      c'2. \bar "||"
      \time 4/4
      c'1 \bar "||"
      \break
      \mark \markup { \bold "D" }
      d'4 d'4 d'4 d'4 \bar "||"
      d'2 d'2 \bar "||"
      \time 3/4
      d'2. \bar "||"
      \time 4/4
      d'1 \bar "|."
    }
    \new Staff \with {
      instrumentName = "Bass"
    } {
      \clef bass
      \time 4/4
      \mark \markup { \bold "B" }
      b4 b4 b4 b4 \bar "||"
      b2 b2 \bar "||"
      \time 3/4
      b2. \bar "||"
      \time 4/4
      b1 \bar "|."
    }
  >>
  \layout {
    indent = 15\mm
  }
}

% ============================================
% TIPS FOR PARENTS
% ============================================

\markup {
  \column {
    \vspace #1.5
    \bold \larger "Tips for Helping Your Child"
    \vspace #0.5
\line { "1." Point to each note and ask your child to name it before they play. }
    \line { "2." Clap the rhythm together before playing - this helps internalise the beat. }
    \line { "3." Use counting words: "ta" for crotchets, "ta-a" for minims, "ta-a-a" for dotted minims, "ta-a-a-a" for semibreves. }
    \line { "4." Look at the note HEAD first (filled or open) to determine the basic length. }
    \line { "5." Check for DOTS - a dot always adds half the value of the note. }
    \line { "6." Practice slowly and count out loud together. }
    \vspace #1
  }
}

\markup {
  \column {
    \bold \larger "Remember"
    \vspace #0.3
    \justify {
      The goal is for your child to instantly recognise these notes and their lengths.
      Regular, short practice sessions work better than long, infrequent ones.
      Make it fun and celebrate small wins!
    }
  }
}
