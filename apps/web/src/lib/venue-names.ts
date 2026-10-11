/** Only published Chinese occupant names belong on the venue display.
 * Do not turn identifiers or placeholder fixture text into attendee names. */
export function chineseVenueName(value: string | null | undefined): string {
  const name = value?.trim() ?? "";
  return /^[\p{Script=Han}\p{White_Space}·・]+$/u.test(name) &&
    /\p{Script=Han}/u.test(name)
    ? name
    : "";
}
