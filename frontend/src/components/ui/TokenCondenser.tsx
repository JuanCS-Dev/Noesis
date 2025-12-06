"use client";

import { useEffect, useState } from "react";

interface TokenCondenserProps {
  text: string;
  className?: string;
  speed?: number;
}

const ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*";

export default function TokenCondenser({ text, className = "", speed = 50 }: TokenCondenserProps) {
  const [displayText, setDisplayText] = useState("");
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    let iteration = 0;
    const interval = setInterval(() => {
      setDisplayText(
        text
          .split("")
          .map((letter, index) => {
            if (index < iteration) {
              return text[index];
            }
            return ALPHABET[Math.floor(Math.random() * ALPHABET.length)];
          })
          .join("")
      );

      if (iteration >= text.length) {
        clearInterval(interval);
        setIsComplete(true);
      }

      iteration += 1 / 2; // Controla a suavidade/velocidade
    }, speed);

    return () => clearInterval(interval);
  }, [text, speed]);

  return (
    <span className={`${className} ${isComplete ? "text-cyan-100" : "text-cyan-600"}`}>
      {displayText}
    </span>
  );
}